export default function StatusBadge({ status }) {
  const colors = {
    SENT: "bg-yellow-600",
    PENDING_SIGNATURE_B: "bg-orange-600",
    PENDING_SIGNATURE_A: "bg-blue-600",
    REJECTED: "bg-red-600",
    ON_BLOCKCHAIN: "bg-green-600",
  };

  return (
    <span
      className={`px-4 py-1 rounded-full text-sm text-[#ECDFCC] ${
        colors[status] || "bg-[#697565]"
      }`}
    >
      {status}
    </span>
  );
}
