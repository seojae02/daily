"use client"

import { Stack, Typography } from "@mui/material"
import { useState } from "react"
import useStoreEdit from "./useStoreEdit"

export default function FourthInfoPage() {
  const aiImageStyles = [
    {
      label: "모던 & 시크",
      imageUrl: "/ai_pre_1.jpg",
      prompts: [
        "깨끗한 흰색 대리석 테이블 위, 밝은 자연광이 들어오는 창가",
        "심플한 무광 회색 배경에 그림자가 부드럽게 지는 구도",
        "차가운 느낌의 콘크리트 질감 바닥, 위에서 아래로 찍는 탑뷰 스타일",
      ],
    },
    {
      label: "따뜻 & 아늑",
      imageUrl: "/ai_pre_2.jpg",
      prompts: [
        "결이 살아있는 따뜻한 원목 테이블, 뒤에는 아늑한 느낌의 벽돌 벽",
        "체크무늬 테이블보 위, 따스한 전구 조명이 비추는 장면",
        "오래된 나무 도마 위, 주변에는 허브나 작은 꽃이 놓인 자연스러운 느낌",
      ],
    },
    {
      label: "고급 & 드라마틱",
      imageUrl: "/ai_pre_3.jpg",
      prompts: [
        "어두운 검은색 배경에 음식 위로만 한 줄기 조명이 떨어지는 극적인 연출",
        "거친 질감의 검은색 돌판 위, 음식의 증기가 피어오르는 모습",
        "짙은 색의 가죽 소파 앞, 낮은 조도의 고급스러운 바(Bar) 분위기",
      ],
    },
    {
      label: "자연 & 건강",
      imageUrl: "/ai_pre_4.jpg",
      prompts: [
        "햇살이 잘 드는 야외 정원의 나무 테이블 위, 싱그러운 잎사귀들",
        "라탄 매트 위, 주변에는 신선한 과일과 채소가 놓인 모습",
        "깨끗한 흰색 천 위, 심플하고 건강한 느낌",
      ],
    },
  ]
  const aiPromotionStyles = [
    {
      label: "친근하고 따뜻한 스타일",
      example:
        "우리 가게는 언제나 여러분을 환영합니다! 편안한 분위기에서 소중한 사람들과 특별한 시간을 보내세요.",
    },
    {
      label: "트렌디하고 감각적인 스타일",
      example:
        "요즘 핫플레이스! 감각적인 인테리어와 인스타 감성 메뉴로 특별한 하루를 만들어보세요.",
    },
    {
      label: "전문적이고 신뢰감 있는 스타일",
      example:
        "20년 경력의 셰프가 직접 만드는 정통 요리! 믿고 먹을 수 있는 최고의 맛을 경험하세요.",
    },
    {
      label: "유쾌하고 재치 있는 스타일",
      example:
        "배고프면 우리 가게로! 맛있게 먹고, 웃으며 즐기는 행복한 시간 보장!",
    },
    {
      label: "프리미엄 & 고급스러운 스타일",
      example:
        "고급스러운 분위기와 엄선된 재료로 만든 프리미엄 메뉴, 소중한 분과의 특별한 만남에 추천합니다.",
    },
    {
      label: "건강 & 웰빙 강조 스타일",
      example:
        "신선한 재료와 건강을 생각한 레시피! 몸과 마음이 모두 만족하는 건강한 한 끼를 만나보세요.",
    },
    {
      label: "가족 친화적 스타일",
      example:
        "아이와 함께, 가족 모두가 즐길 수 있는 넓고 안전한 공간! 가족 외식은 우리 가게에서.",
    },
  ]

  const { contentFeel, setContentFeel } = useStoreEdit()
  const [selectedPicIdx, setSelectedPicIdx] = useState<number | null>(null)

  const [selectedPostIdx, setSelectedPostIdx] = useState<number | null>(null)

  // 이미지 스타일 선택 시 프롬프트 저장
  const handlePicFeelSelect = (styleIdx: number) => {
    setSelectedPicIdx(styleIdx)
    setContentFeel({
      ...contentFeel,
      picFeel: aiImageStyles[styleIdx].prompts.join(","),
    })
  }

  const handlePostFeelSelect = (idx: number) => {
    setSelectedPostIdx(idx)
    setContentFeel({
      ...contentFeel,
      postFeel: aiPromotionStyles[idx].label,
    })
  }

  return (
    <Stack width="100%" height="100%" alignItems="center">
      <Stack textAlign="center">
        4. 원하시는 컨텐츠 느낌을 <br />
        선택해주세요.
      </Stack>

      <Stack gap="16px" width="100%" maxWidth="400px" padding="12px" mt="24px">
        <Typography
          px="12px"
          variant="body2"
          color="text.secondary"
          width="100%"
          sx={{ textAlign: "left" }}
        >
          사진 스타일 및 프롬프트
        </Typography>
        <Stack gap="16px" direction="row" overflow="scroll" width="100vw">
          {aiImageStyles.map((style, styleIdx) => (
            <Stack key={styleIdx}>
              <Typography variant="subtitle2" color="primary" sx={{ mb: 1 }}>
                {style.label}
              </Typography>
              <Stack direction="row" gap="8px">
                <Stack
                  minWidth="140px"
                  height="180px"
                  bgcolor={selectedPicIdx === styleIdx ? "#e3f2fd" : "#f0f0f0"}
                  borderRadius="8px"
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                  sx={{
                    cursor: "pointer",
                    border:
                      selectedPicIdx === styleIdx
                        ? "2px solid #1976D2"
                        : "1px solid #ccc",
                  }}
                  onClick={() => handlePicFeelSelect(styleIdx)}
                >
                  <img
                    src={style.imageUrl}
                    alt={style.label}
                    style={{ maxHeight: "100%", maxWidth: "100%" }}
                  />
                </Stack>
              </Stack>
            </Stack>
          ))}
        </Stack>

        <Typography
          px="12px"
          variant="body2"
          color="text.secondary"
          width="100%"
          sx={{
            textAlign: "left",
            mt: 2,
          }}
        >
          게시글 느낌
        </Typography>
        <Stack width="100%" overflow="scroll" gap="12px">
          {aiPromotionStyles.map((style, index) => (
            <Stack
              key={index}
              minWidth="200px"
              height="auto"
              bgcolor={selectedPostIdx === index ? "#e3f2fd" : "#f0f0f0"}
              borderRadius="8px"
              display="flex"
              flexDirection="column"
              alignItems="flex-start"
              justifyContent="center"
              sx={{
                cursor: "pointer",
                border:
                  selectedPostIdx === index
                    ? "2px solid #1976D2"
                    : "1px solid #ccc",
                p: 2,
              }}
              onClick={() => handlePostFeelSelect(index)}
            >
              <Typography variant="subtitle2" color="primary" sx={{ mb: 1 }}>
                {style.label}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {style.example}
              </Typography>
            </Stack>
          ))}
        </Stack>
      </Stack>
    </Stack>
  )
}
