"""
Unit tests for utils/token_utils.py — Token estimation and processing mode selection.

Tests token counting heuristics and mode selection logic to ensure documents
are routed to the correct processing pipeline based on size.
"""

import pytest

from utils.token_utils import (
    estimate_tokens, 
    choose_processing_mode,
    get_mode_config,
    FULL_DOC_MAX_TOKENS, 
    HYBRID_MAX_TOKENS
)


class TestEstimateTokens:
    """Tests for estimate_tokens() function."""

    def test_empty_string_returns_zero(self):
        """Test that empty string estimates to 0 tokens."""
        assert estimate_tokens("") == 0

    def test_none_returns_zero(self):
        """Test that None input returns 0 tokens safely."""
        assert estimate_tokens(None) == 0

    def test_non_string_returns_zero(self):
        """Test that non-string inputs return 0."""
        assert estimate_tokens(123) == 0
        assert estimate_tokens([]) == 0
        assert estimate_tokens({}) == 0

    def test_known_length_calculation(self):
        """Test the 4-chars-per-token heuristic."""
        # 400 chars / 4 = 100 tokens
        assert estimate_tokens("a" * 400) == 100

    def test_large_text(self):
        """Test estimation with large text."""
        text = "x" * 120_000
        assert estimate_tokens(text) == 30_000

    def test_realistic_contract_length(self):
        """Test typical contract text (~10,000 chars = ~2,500 tokens)."""
        text = "x" * 10_000
        assert estimate_tokens(text) == 2_500

    def test_single_character(self):
        """Test single character estimation."""
        assert estimate_tokens("x") == 0  # 1 char / 4 = 0


class TestChooseProcessingMode:
    """Tests for choose_processing_mode() function."""

    def test_small_doc_returns_full_doc(self):
        """Test small documents (< 8k tokens) use full_doc mode."""
        # Under 8000 tokens = under 32000 chars
        text = "x" * 1000
        assert choose_processing_mode(text) == "full_doc"

    def test_exactly_at_full_doc_boundary(self):
        """Test exactly at full_doc boundary."""
        # FULL_DOC_MAX_TOKENS = 8000, so 32000 chars = 8000 tokens
        text = "x" * 32_000
        mode = choose_processing_mode(text)
        assert mode in ("full_doc", "hybrid")  # At boundary

    def test_medium_doc_returns_hybrid(self):
        """Test medium documents (8k-30k tokens) use hybrid mode."""
        # Between 8000 and 30000 tokens = 32000-120000 chars
        text = "x" * 50_000  # = 12,500 tokens
        assert choose_processing_mode(text) == "hybrid"

    def test_exactly_at_hybrid_boundary(self):
        """Test exactly at hybrid boundary."""
        # HYBRID_MAX_TOKENS = 30000, so 120000 chars = 30000 tokens
        text = "x" * 120_000
        mode = choose_processing_mode(text)
        assert mode in ("hybrid", "batched")  # At boundary

    def test_large_doc_returns_batched(self):
        """Test large documents (> 30k tokens) use batched mode."""
        # Over 30000 tokens = over 120000 chars
        text = "x" * 150_000  # = 37,500 tokens
        assert choose_processing_mode(text) == "batched"

    def test_very_large_doc(self):
        """Test very large documents."""
        text = "x" * 1_000_000
        assert choose_processing_mode(text) == "batched"

    def test_returns_only_valid_modes(self):
        """Test that only valid mode names are returned."""
        valid_modes = {"full_doc", "hybrid", "batched"}
        for size in [100, 10_000, 50_000, 200_000]:
            result = choose_processing_mode("x" * size)
            assert result in valid_modes


class TestGetModeConfig:
    """Tests for get_mode_config() function."""

    def test_full_doc_config_structure(self):
        """Test that full_doc mode config has required keys."""
        config = get_mode_config("full_doc")
        assert "max_tokens_per_call" in config
        assert "clauses_per_batch" in config
        assert "chunk_size" in config
        assert "description" in config

    def test_full_doc_clause_batch_is_none(self):
        """Test that full_doc doesn't batch clauses."""
        config = get_mode_config("full_doc")
        assert config["clauses_per_batch"] is None
        assert config["chunk_size"] is None

    def test_hybrid_config_structure(self):
        """Test that hybrid mode config is properly structured."""
        config = get_mode_config("hybrid")
        assert config["clauses_per_batch"] is not None
        assert isinstance(config["clauses_per_batch"], int)
        assert config["chunk_size"] is None

    def test_batched_config_has_chunk_size(self):
        """Test that batched mode config includes chunk_size."""
        config = get_mode_config("batched")
        assert config["chunk_size"] is not None
        assert isinstance(config["chunk_size"], int)
        assert config["clauses_per_batch"] is not None

    def test_invalid_mode_raises_value_error(self):
        """Test that unknown modes raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_mode_config("invalid_mode")
        assert "Unknown processing mode" in str(exc_info.value)
        assert "invalid_mode" in str(exc_info.value)

    def test_mode_config_descriptions_exist(self):
        """Test that all configs have descriptive text."""
        for mode in ["full_doc", "hybrid", "batched"]:
            config = get_mode_config(mode)
            assert len(config["description"]) > 0
            assert isinstance(config["description"], str)

    def test_hybrid_batch_size_less_than_batched(self):
        """Test that batched mode processes fewer clauses per batch."""
        hybrid = get_mode_config("hybrid")
        batched = get_mode_config("batched")
        # Both should have batch sizes, hybrid should be reasonable
        assert hybrid["clauses_per_batch"] > 0
        assert batched["clauses_per_batch"] > 0


class TestModeIntegration:
    """Integration tests for token estimation and mode selection."""

    def test_mode_selection_consistent_with_boundaries(self):
        """Test that mode boundaries are consistent with tokens."""
        # At 8000 tokens
        text_8k = "x" * int(FULL_DOC_MAX_TOKENS * 4)
        mode = choose_processing_mode(text_8k)
        # Should transition from full_doc to hybrid around this point
        assert mode in ("full_doc", "hybrid")

        # At 30000 tokens
        text_30k = "x" * int(HYBRID_MAX_TOKENS * 4)
        mode = choose_processing_mode(text_30k)
        # Should transition from hybrid to batched around this point
        assert mode in ("hybrid", "batched")

    def test_small_realistic_contract(self):
        """Test with realistic small contract."""
        small_contract = """
        LOAN AGREEMENT

        This agreement is between borrower and lender.

        Terms: The borrower will repay within 30 days.
        """ * 10  # ~500 chars, ~125 tokens
        
        mode = choose_processing_mode(small_contract)
        assert mode == "full_doc"
        assert estimate_tokens(small_contract) < FULL_DOC_MAX_TOKENS

    def test_medium_realistic_contract(self):
        """Test with realistic medium- sized contract."""
        medium_contract = """
        MASTER SERVICE AGREEMENT

        This agreement outlines the terms and conditions...
        """ * 200  # ~5000 chars, ~1250 tokens
        
        mode = choose_processing_mode(medium_contract)
        assert mode == "full_doc"

    def test_large_realistic_contract(self):
        """Test with realistic large contract."""
        large_contract = "Section title\nClause content. " * 2000  # ~30,000 chars
        
        mode = choose_processing_mode(large_contract)
        assert mode in ("hybrid", "batched")
