import type { Transaction } from "@/lib/types"
import { formatKrw } from "@/lib/format"

interface TransactionListProps {
  transactions: Transaction[]
}

const STATUS_LABEL: Record<string, string> = {
  requested: "요청됨",
  accepted: "수락됨",
  rejected: "거절됨",
  completed: "완료",
  cancelled: "취소됨",
}

export default function TransactionList({ transactions }: TransactionListProps) {
  if (transactions.length === 0) {
    return <p className="text-sm text-ink-muted">등록된 거래 요청이 없습니다.</p>
  }

  return (
    <div className="overflow-x-auto rounded border border-line">
      <table className="w-full min-w-[560px] text-sm">
        <thead>
          <tr className="border-b border-line bg-paper-raised text-left text-xs text-ink-muted">
            <th className="px-3 py-2 font-normal">거래처 유형</th>
            <th className="px-3 py-2 font-normal text-right">수량</th>
            <th className="px-3 py-2 font-normal text-right">단가</th>
            <th className="px-3 py-2 font-normal text-right">순수익</th>
            <th className="px-3 py-2 font-normal">상태</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((txn) => (
            <tr key={txn.id} className="border-b border-line last:border-0">
              <td className="px-3 py-2 text-ink">{txn.counterparty_type === "wholesaler" ? "도매처" : "판매처"}</td>
              <td className="px-3 py-2 text-right font-data text-ink-muted">
                {txn.quantity_kg.toLocaleString("ko-KR")}kg
              </td>
              <td className="px-3 py-2 text-right font-data text-ink-muted">
                {formatKrw(txn.unit_price_krw_per_kg)}
              </td>
              <td className="px-3 py-2 text-right font-data text-status-good">
                {txn.net_profit_krw !== null ? formatKrw(txn.net_profit_krw) : "-"}
              </td>
              <td className="px-3 py-2 text-ink-muted">{STATUS_LABEL[txn.status] ?? txn.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
