import grpc
from concurrent import futures
import tempfile
import os
import uuid
import sys
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Try to load either .env or the 'env' file the user has open
load_dotenv(".env")
load_dotenv("env")

# MacOS SSL Cert Fix
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

import contract_pb2
import contract_pb2_grpc
from services.pipeline import run_pipeline

# ─── LOGGING CONFIGURATION ───────────────────────────────────────────

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, "grpc_server.log")

# Setup root logger
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("GRPCServer")

def safe_log_info(msg):
    try: logger.info(msg)
    except: pass

def safe_log_error(msg):
    try: logger.error(msg)
    except: pass

# ─── REDIRECT STDOUT/STDERR TO LOG FILE ──────────────────────────────
# This prevents [Errno 5] Input/output error on macOS when terminal is stale
class UncrashableStream:
    def __init__(self, original_stream, log_func):
        self.original_stream = original_stream
        self.log_func = log_func

    def write(self, data):
        if data.strip():
            self.log_func(data.strip())
        try:
            self.original_stream.write(data)
            self.original_stream.flush()
        except OSError:
            pass # Ignore Errno 5

    def flush(self):
        try: self.original_stream.flush()
        except OSError: pass

    def __getattr__(self, attr):
        return getattr(self.original_stream, attr)

sys.stdout = UncrashableStream(sys.stdout, safe_log_info)
sys.stderr = UncrashableStream(sys.stderr, safe_log_error)

class AnalyzerService(contract_pb2_grpc.ContractAnalyzerServicer):
    def AnalyzeDocument(self, request, context):
        print(f"📥 Received document for analysis: length={len(request.file_bytes)} extension={request.file_extension}")
        
        # Save bytes to a temp file
        ext = request.file_extension if request.file_extension.startswith(".") else f".{request.file_extension}"
        temp_path = os.path.join(tempfile.gettempdir(), f"contract_{uuid.uuid4().hex}{ext}")
        
        try:
            with open(temp_path, "wb") as f:
                f.write(request.file_bytes)
            
            # Execute standard pipeline
            print("🚀 Executing deep LegalT AI pipeline...")
            result_dict = run_pipeline(temp_path, verbose=False)
            
            print("✅ Pipeline returned successfully. Mapping to Protobuf structure...")
            
            # Build Pydantic-like mapping to Protobuf
            meta = result_dict.get("metadata", {})
            metadata_pb = contract_pb2.DocumentTypeMetadata(
                document_type=meta.get("document_type") or "",
                document_subtype=meta.get("document_subtype") or "",
                jurisdiction=meta.get("jurisdiction") or "",
                governing_law=meta.get("governing_law") or ""
            )
            
            risks_pb = []
            for r in result_dict.get("risks", []):
                risks_pb.append(contract_pb2.RiskItem(
                    clause_id=r.get("clause_id") or "",
                    risk_type=r.get("risk_type") or "",
                    severity=r.get("severity") or "LOW",
                    reason=r.get("reason") or "",
                    impacted_party=r.get("impacted_party") or "",
                    risk_sentence=r.get("risk_sentence") or "",
                    suggestion=r.get("suggestion") or "",
                    legal_precedent=r.get("legal_precedent") or "",
                    risk_labels=r.get("risk_labels") or [],
                    risk_context=r.get("risk_context") or ""
                ))
                
            missing_pb = []
            for m in result_dict.get("missing_clauses", []):
                missing_pb.append(contract_pb2.MissingClause(
                    clause_type=m.get("clause_type") or "",
                    importance=m.get("importance") or "LOW",
                    reason_needed=m.get("reason_needed") or "",
                    suggested_language=m.get("suggested_language") or ""
                ))
                
            neg_pb = []
            for n in result_dict.get("negotiation_points", []):
                neg_pb.append(contract_pb2.NegotiationPoint(
                    issue=n.get("issue") or "",
                    clause_id=n.get("clause_id") or "",
                    favorable_to=n.get("favorable_to") or "",
                    disadvantaged_party=n.get("disadvantaged_party") or "",
                    leverage=n.get("leverage") or "",
                    suggested_counter=n.get("suggested_counter") or ""
                ))
            
            summary_dict = result_dict.get("summary", {})
            summary_pb = contract_pb2.DocumentSummary(
                executive_summary=summary_dict.get("executive_summary") or "",
                key_points=summary_dict.get("key_points") or [],
                red_flags=summary_dict.get("red_flags") or [],
                favorable_clauses=summary_dict.get("favorable_clauses") or [],
                unusual_clauses=summary_dict.get("unusual_clauses") or [],
                favorable_to=summary_dict.get("favorable_to") or "",
                overall_risk_score=summary_dict.get("overall_risk_score") or 0,
                recommended_actions=summary_dict.get("recommended_actions") or []
            )

            response = contract_pb2.AnalysisResponse(
                success=True,
                document_id=result_dict.get("document_id") or "",
                analyzed_at=result_dict.get("analyzed_at") or "",
                metadata=metadata_pb,
                risks=risks_pb,
                missing_clauses=missing_pb,
                negotiation_points=neg_pb,
                summary=summary_pb
            )
            
            return response
            
        except Exception as e:
            error_msg = str(e)
            safe_log_error(f"❌ Pipeline failed: {error_msg}")
            
            try:
                import traceback
                trace_str = traceback.format_exc()
                safe_log_error(trace_str)
            except:
                pass
                
            return contract_pb2.AnalysisResponse(
                success=False,
                error_message=error_msg
            )
        finally:
            if os.path.exists(temp_path):
                try: os.remove(temp_path)
                except: pass

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    contract_pb2_grpc.add_ContractAnalyzerServicer_to_server(AnalyzerService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    safe_log_info("🚀 gRPC Analysis Server running on [::]:50051 ...")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
