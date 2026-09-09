import type { Metadata } from "next"
import { Geist_Mono, Noto_Sans_KR, Noto_Serif_KR } from "next/font/google"
import ChatPanel from "@/components/ChatPanel"
import "./globals.css"

const notoSerifKr = Noto_Serif_KR({
  variable: "--font-noto-serif-kr",
  subsets: ["latin"],
  weight: ["600", "700"],
})

const notoSansKr = Noto_Sans_KR({
  variable: "--font-noto-sans-kr",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
})

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
})

export const metadata: Metadata = {
  title: "울퉁불퉁 농장 AI",
  description: "휴경농지, 스마트팜, 농산물 유통 데이터를 하나로 묶는 AI 생산-유통 플랫폼",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="ko">
      <body
        className={`${notoSerifKr.variable} ${notoSansKr.variable} ${geistMono.variable} antialiased`}
      >
        {children}
        <ChatPanel />
      </body>
    </html>
  )
}
