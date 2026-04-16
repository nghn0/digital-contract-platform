export default function StatusBadge({ status }) {
  const colors = {
    SENT: "bg-yellow-600",
    AWAITING_RECEIVER_SIGNATURE: "bg-orange-600",
    AWAITING_SENDER_SIGNATURE: "bg-blue-600",
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
