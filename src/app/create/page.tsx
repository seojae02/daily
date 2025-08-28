"use client"

import React, { useState, ChangeEvent, useEffect } from "react"
import {
  Box,
  Container,
  Typography,
  Paper,
  Select,
  MenuItem,
  FormControl,
  Button,
  TextField,
  Stack,
  Chip,
  CircularProgress,
} from "@mui/material"
import UserProfileHeader from "../components/UserProfileHeader"
import AddPhotoAlternateIcon from "@mui/icons-material/AddPhotoAlternate"
import { useAtom, useSetAtom } from "jotai"
import { creationResultAtom } from "./atom/creationAtom"
import { useRouter } from "next/navigation"
import axiosInstance from "@/config/axios" // 백엔드 서버용
import aiAxiosInstance from "@/config/aiAxiosInstance" // AI 서버용
import { StoreInfo } from "../info/edit/useStoreEdit"

const aiImageStyles = [
  {
    label: "모던 & 시크",
    prompts: [
      "깨끗한 흰색 대리석 테이블 위, 밝은 자연광이 들어오는 창가",
      "심플한 무광 회색 배경에 그림자가 부드럽게 지는 구도",
      "차가운 느낌의 콘크리트 질감 바닥, 위에서 아래로 찍는 탑뷰 스타일",
    ],
  },
  {
    label: "따뜻 & 아늑",
    prompts: [
      "결이 살아있는 따뜻한 원목 테이블, 뒤에는 아늑한 느낌의 벽돌 벽",
      "체크무늬 테이블보 위, 따스한 전구 조명이 비추는 장면",
      "오래된 나무 도마 위, 주변에는 허브나 작은 꽃이 놓인 자연스러운 느낌",
    ],
  },
  {
    label: "고급 & 드라마틱",
    prompts: [
      "어두운 검은색 배경에 음식 위로만 한 줄기 조명이 떨어지는 극적인 연출",
      "거친 질감의 검은색 돌판 위, 음식의 증기가 피어오르는 모습",
      "짙은 색의 가죽 소파 앞, 낮은 조도의 고급스러운 바(Bar) 분위기",
    ],
  },
  {
    label: "자연 & 건강",
    prompts: [
      "햇살이 잘 드는 야외 정원의 나무 테이블 위, 싱그러운 잎사귀들",
      "라탄 매트 위, 주변에는 신선한 과일과 채소가 놓인 모습",
      "깨끗한 흰색 천 위, 심플하고 건강한 느낌",
    ],
  },
]

const aiPromotionStyles = [
  { label: "친근하고 따뜻한 스타일" },
  { label: "트렌디하고 감각적인 스타일" },
  { label: "전문적이고 신뢰감 있는 스타일" },
  { label: "유쾌하고 재치 있는 스타일" },
  { label: "프리미엄 & 고급스러운 스타일" },
  { label: "건강 & 웰빙 강조 스타일" },
  { label: "가족 친화적 스타일" },
]

function CreateContentPage() {
  const router = useRouter()
  const setCreationResult = useSetAtom(creationResultAtom)
  const [contentType, setContentType] = useState("blog") // 업로드 종류
  const [mood, setMood] = useState("") // 오늘의 느낌
  const [feel, setFeel] = useState("") // 오늘의 느낌
  const [info, setInfo] = useState("") // 오늘의 정보
  const [directContent, setDirectContent] = useState("") // 내용 직접 입력
  const [hashtags, setHashtags] = useState<string[]>(["#해시태그"]) // chip 해시태그 배열 관리
  const [userTags, setUserTags] = useState<string[]>(["@someone_"]) // chip 유저태그 배열 관리
  const [currentHashtag, setCurrentHashtag] = useState("") // 해시태그 현재 입력값 저장
  const [currentUserTag, setCurrentUserTag] = useState("") // 유저태그 현재 입력값 저장
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [storeInfo, setStoreInfo] = useState<StoreInfo | null>(null) // 가게 정보

  useEffect(() => {
    fetchContentFeel()
  }, [])

  async function fetchContentFeel() {
    const storeId = localStorage.getItem("storeId")
    const { data, status } = await axiosInstance.get<{
      storeId: number
      picFeel: string
      postFeel: string
    }>(`/contents?storeId=${storeId}`)

    setMood(data.picFeel || "모던 & 시크")
    setFeel(data.postFeel || "친근하고 따뜻한 스타일")

    axiosInstance
      .get<{ url: StoreInfo }>(`/store?storeId=${storeId}`)
      .then(({ data, status }) => {
        if (status === 200) {
          setStoreInfo(data.url)
        }
      })

    return status
  }

  // 해시태그 기능 구현
  // 'Enter' 키로 해시태그를 추가
  const handleHashtagKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "Enter" && currentHashtag.trim() !== "") {
      event.preventDefault()
      setHashtags([...hashtags, `#${currentHashtag.trim()}`])
      setCurrentHashtag("")
    }
  }

  // x 버튼으로 해시태그를 삭제
  const handleHashtagDelete = (tagToDelete: string) => {
    setHashtags(hashtags.filter((tag) => tag !== tagToDelete))
  }

  // 유저태그 기능 구현
  const handleUserTagKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "Enter" && currentUserTag.trim() !== "") {
      event.preventDefault()
      setUserTags([...userTags, `@${currentUserTag.trim()}`])
      setCurrentUserTag("")
    }
  }

  const handleUserTagDelete = (tagToDelete: string) => {
    setUserTags(userTags.filter((tag) => tag !== tagToDelete))
  }

  // 사진 선택
  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0])
    }
  }

  // [수정됨] 결과물 실행 함수
  const handleCreate = async () => {
    if (!selectedFile) {
      alert("이미지를 먼저 선택해주세요!")
      return
    }

    setIsLoading(true)

    try {
      const formData = new FormData()

      formData.append("input_image", selectedFile)
      formData.append("user_prompt", mood)

      console.log("이미지 가공 요청")
      const { data } = await aiAxiosInstance.post("/v1/outpaint", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        responseType: "blob",
      })
      console.log("이미지 가공 요청 완료")
      const imageUrl = URL.createObjectURL(data)
      const promoParams = new URLSearchParams()

      promoParams.append("store_name", storeInfo?.name || "") // *실제 가게 이름으로 변경 필요
      promoParams.append(
        "mood",
        feel + " 그리고 아래 정보들을 추가해줘 " + info
      )
      promoParams.append("store_description", storeInfo?.description || "")
      promoParams.append("location_text", storeInfo?.location || "")

      const promoResponse = await aiAxiosInstance.post(
        "/v1/generate-promo",
        promoParams
      )
      console.log("AI 텍스트 생성 API 실제 응답:", promoResponse.data)

      const aiResult = promoResponse.data

      if (aiResult && aiResult.variants && aiResult.variants.length > 0) {
        const processedVariants = aiResult.variants.map(
          (variant: {
            headline: string
            body: string
            cta: string
            tags?: string[]
          }) => {
            return {
              headline: variant.headline,
              body: variant.body
                .split(/(https?:\/\/[^\s]+)/g)
                .filter(Boolean) as string[],
              cta: variant.cta,
              hashtags: variant.tags || [],
              originalBody: variant.body, // 원본 본문 추가
            }
          }
        )

        // 가공된 결과물 배열 전체를 atom에 저장합니다.
        setCreationResult({
          imageUrl: imageUrl,
          mood: mood,
          variants: processedVariants,
        })

        router.push("/create/result")
      } else {
        throw new Error("AI가 텍스트를 생성하지 못했습니다.")
      }
    } catch (error) {
      console.error("콘텐츠 제작에 실패했습니다:", error)
      alert("콘텐츠 제작 중 오류가 발생했습니다. 다시 시도해주세요.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Container maxWidth="sm" sx={{ p: 0, pb: 7 }}>
      {/* 기존 헤더 재사용 */}
      <UserProfileHeader />
      <Box sx={{ p: 2 }}>
        <Paper elevation={2} sx={{ p: 3, borderRadius: 3 }}>
          <Stack spacing={3}>
            {/* 콘텐츠 종류 선택 드롭다운 */}
            <Stack
              direction="row"
              spacing={1}
              alignItems="center"
              justifyContent="space-between"
            >
              <FormControl variant="filled" size="small" sx={{ minWidth: 150 }}>
                <Select
                  value={contentType}
                  onChange={(e) => setContentType(e.target.value)}
                  sx={{
                    ".MuiSelect-select": {
                      paddingTop: "10px",
                      paddingBottom: "10px",
                    },
                  }}
                >
                  <MenuItem value="blog">블로그</MenuItem>
                  <MenuItem value="story">스토리</MenuItem>
                  <MenuItem value="feed">피드</MenuItem>
                </Select>
              </FormControl>
              {/* 제작 버튼 */}
              <Button
                variant="contained"
                size="large"
                onClick={handleCreate}
                disabled={isLoading}
                sx={{
                  backgroundColor: "grey.200",
                  color: "black",
                  "&:hover": { backgroundColor: "grey.300" },
                }}
              >
                {isLoading ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  "제작"
                )}
              </Button>
            </Stack>

            {/* 오늘의 느낌 선택 드롭다운 */}
            <Box>
              <Typography variant="body1" fontWeight="bold" sx={{ mb: 1 }}>
                이미지의 느낌
              </Typography>
              <FormControl fullWidth>
                <Select value={mood} onChange={(e) => setMood(e.target.value)}>
                  {aiImageStyles.map((style, index) => (
                    <MenuItem key={index} value={style.prompts.join(",")}>
                      {style.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>

            <Box>
              <Typography variant="body1" fontWeight="bold" sx={{ mb: 1 }}>
                게시글의 느낌
              </Typography>
              <FormControl fullWidth>
                <Select value={feel} onChange={(e) => setFeel(e.target.value)}>
                  {aiPromotionStyles.map((style, index) => (
                    <MenuItem key={index} value={style.label}>
                      {style.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>

            {/* 오늘의 정보 입력 */}
            <Box>
              <Typography variant="body1" fontWeight="bold" sx={{ mb: 1 }}>
                오늘의 정보
              </Typography>
              <TextField
                multiline
                rows={4}
                value={info}
                onChange={(e) => setInfo(e.target.value)}
                placeholder="AI에게 전달할 간단한 정보를 입력해주세요.&#10;예: 오늘부터 애플파이 판매 시작!"
                fullWidth
              />
            </Box>

            {/* '피드'가 선택되었을 때, '내용 직접 입력' 창 보이기*/}
            {contentType === "feed" && (
              <Box>
                <Typography variant="body1" fontWeight="bold" sx={{ mb: 1 }}>
                  내용 직접 입력
                </Typography>
                <TextField
                  multiline
                  rows={6}
                  value={directContent}
                  onChange={(e) => setDirectContent(e.target.value)}
                  placeholder="피드에 들어갈 내용을 직접 입력해주세요."
                  fullWidth
                />
              </Box>
            )}

            {/* 사진 추가 */}
            <Box>
              <Typography variant="body1" fontWeight="bold" sx={{ mb: 1 }}>
                사진 추가
              </Typography>
              <Stack direction="row" spacing={2}>
                <Button
                  variant="outlined"
                  component="label"
                  sx={{
                    width: 120,
                    height: 120,
                    display: "flex",
                    flexDirection: "column",
                    color: "text.secondary",
                    borderColor: "grey.400",
                  }}
                >
                  <AddPhotoAlternateIcon />
                  사진 선택
                  <input
                    type="file"
                    accept="image/*"
                    hidden
                    onChange={handleFileChange}
                  />
                </Button>
                {selectedFile && (
                  <Typography variant="body2" noWrap>
                    {selectedFile.name}
                  </Typography>
                )}
              </Stack>
            </Box>

            {/* 해시태그 */}
            {contentType !== "blog" && (
              <>
                <Box>
                  <Typography variant="body1" fontWeight="bold" sx={{ mb: 1 }}>
                    해시태그 입력
                  </Typography>
                  {/* 추가된 태그들을 Chip으로 보여주는 영역 */}
                  <Stack
                    direction="row"
                    spacing={1}
                    sx={{ mb: 1, flexWrap: "wrap", gap: 1 }}
                  >
                    {hashtags.map((tag) => (
                      <Chip
                        key={tag}
                        label={tag}
                        onDelete={() => handleHashtagDelete(tag)}
                      />
                    ))}
                  </Stack>
                  {/* 새로운 태그를 입력하는 TextField 영역 */}
                  <TextField
                    variant="outlined"
                    size="small"
                    fullWidth
                    value={currentHashtag}
                    onChange={(e) => setCurrentHashtag(e.target.value)}
                    onKeyDown={handleHashtagKeyDown}
                    placeholder="태그 입력 후 엔터키로 업로드"
                  />
                </Box>

                {/* 다른 사람 태그 */}
                <Box>
                  <Typography variant="body1" fontWeight="bold" sx={{ mb: 1 }}>
                    다른 사람 태그
                  </Typography>
                  {/* 추가된 태그들을 Chip으로 보여주는 영역 */}
                  <Stack
                    direction="row"
                    spacing={1}
                    sx={{ mb: 1, flexWrap: "wrap", gap: 1 }}
                  >
                    {userTags.map((tag) => (
                      <Chip
                        key={tag}
                        label={tag}
                        onDelete={() => handleUserTagDelete(tag)}
                      />
                    ))}
                  </Stack>
                  {/* 새로운 태그를 입력하는 TextField 영역 */}
                  <TextField
                    variant="outlined"
                    size="small"
                    fullWidth
                    value={currentUserTag}
                    onChange={(e) => setCurrentUserTag(e.target.value)}
                    onKeyDown={handleUserTagKeyDown}
                    placeholder="유저 입력 후 엔터키로 업로드"
                  />
                </Box>
              </>
            )}
          </Stack>
        </Paper>
      </Box>
    </Container>
  )
}

export default CreateContentPage
