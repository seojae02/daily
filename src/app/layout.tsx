import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import ThemeRegistry from './theme/ThemeRegistry';
import MainBottomNav from './components/MainBottomNav'; 
import { Stack } from "@mui/material"

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
})

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
})

export const metadata: Metadata = {
  title: "Daily Alley",
  description: "우리 동네를 살리는 AI 브랜딩 솔루션",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="ko">
      <body>
        <ThemeRegistry>
          {/* 메인 콘텐츠 영역 */}
          <Stack height="100vh" width="100%">
            <Stack flex="1" overflow="auto">
              {children}
            </Stack>
            {/* 하단 네비게이션 바 */}
            <MainBottomNav />
          </Stack>
        </ThemeRegistry>
      </body>
    </html>
  )
}
