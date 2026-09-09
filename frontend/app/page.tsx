import Header from "@/components/Header"
import EntryCard from "@/components/EntryCard"

export default function Home() {
  return (
    <div className="min-h-screen bg-paper">
      <Header />
      <main className="mx-auto max-w-6xl px-6 py-8">
        <section className="field-grid rounded border border-line bg-paper-raised px-8 py-14">
          <p className="text-sm text-forest-deep">생산부터 유통까지 하나의 흐름으로</p>
          <h1 className="mt-2 max-w-xl font-display text-4xl font-bold leading-tight text-ink">
            휴경농지와 스마트팜, 유통을 잇는 AI 워크스테이션
          </h1>
          <p className="mt-4 max-w-lg text-sm text-ink-muted">
            시세를 예측하고 도매처를 추천하며, 방치된 농지를 새 농업인과 연결합니다.
            아래에서 역할에 맞는 화면으로 이동하세요.
          </p>
        </section>

        <section aria-labelledby="entry-heading" className="mt-8">
          <h2 id="entry-heading" className="sr-only">
            화면 선택
          </h2>
          <div className="grid gap-4 sm:grid-cols-3">
            <EntryCard
              href="/farm"
              title="농가 대시보드"
              description="현재 작물, 예상 수확량, 스마트팜 상태와 AI 추천 도매처를 확인합니다."
              accent="#2f5233"
            />
            <EntryCard
              href="/distributor"
              title="유통업체 대시보드"
              description="AI가 추천한 농가와 시장 분석을 보고 거래를 요청합니다."
              accent="#b98a1d"
            />
            <EntryCard
              href="/idle-land"
              title="유휴토지 지도"
              description="휴경농지 현황을 지도에서 확인하고 조건을 비교합니다."
              accent="#a24328"
            />
          </div>
        </section>
      </main>
    </div>
  )
}
