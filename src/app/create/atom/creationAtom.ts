import { atom } from "jotai"

// 단일 결과물의 타입을 정의합니다.
export interface AiCreationVariant {
  headline: string // 제목
  body: string[] // 본문 (이미지 URL을 기준으로 분리된 배열)
  cta: string // 행동 유도 문구
  hashtags: string[] // 해시태그
  originalBody: string // 원본 본문
}

// AI로부터 받은 전체 결과물을 저장할 타입을 정의합니다.
export interface AiGenerationResult {
  imageUrl: string // 생성된 대표 이미지
  mood: string // 생성 시 선택했던 분위기
  variants: AiCreationVariant[] // 여러 개의 생성 결과물 배열
}

// 기존 atom을 새로운 타입으로 변경합니다.
export const creationResultAtom = atom<AiGenerationResult | null>(null)
