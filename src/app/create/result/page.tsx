"use client"

import React, { useEffect, useState } from "react"
import {
  Box,
  Container,
  Typography,
  Button,
  Divider,
  Paper,
  Stack,
  Chip,
  IconButton,
  CircularProgress,
} from "@mui/material"
import UserProfileHeader from "../../components/UserProfileHeader"
import { useAtom } from "jotai"
import { creationResultAtom } from "../atom/creationAtom"
import { useRouter } from "next/navigation"
import ArrowBackIcon from "@mui/icons-material/ArrowBack"
import NavigateNextIcon from "@mui/icons-material/NavigateNext"
import NavigateBeforeIcon from "@mui/icons-material/NavigateBefore"
import axiosInstance from "@/config/axios"

function CreateResultPage() {
  const router = useRouter()
  const [creationResult, setCreationResult] = useAtom(creationResultAtom)

  // 현재 보여줄 결과물의 인덱스를 관리
  const [currentIndex, setCurrentIndex] = useState(0)
  // 업로드 상태를 관리
  const [isUploading, setIsUploading] = useState(false)

  useEffect(() => {
    if (!creationResult) {
      router.replace("/create")
    }
  }, [creationResult, router])

  // 현재 인덱스에 해당하는 결과물을 쉽게 사용하기 위한 변수
  const currentVariant = creationResult?.variants[currentIndex]

  // 다음 결과물을 보여주는 함수
  const handleNextResult = () => {
    if (creationResult && currentIndex < creationResult.variants.length - 1) {
      setCurrentIndex(currentIndex + 1)
    }
  }

  // 이전 결과물을 보여주는 함수
  const handlePrevResult = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1)
    }
  }

  // 해시태그 삭제 기능
  const handleHashtagDelete = (tagToDelete: string) => {
    if (creationResult && currentVariant) {
      const updatedHashtags = currentVariant.hashtags.filter(
        (tag) => tag !== tagToDelete
      )

      const updatedVariants = [...creationResult.variants]
      updatedVariants[currentIndex] = {
        ...currentVariant,
        hashtags: updatedHashtags,
      }

      setCreationResult({ ...creationResult, variants: updatedVariants })
    }
  }

  // 기존 DB 저장 함수
  const handleUpload = async () => {
    if (!creationResult || !currentVariant) {
      alert("업로드할 콘텐츠가 없습니다.")
      return
    }

    setIsUploading(true)

    try {
      const fullTextContent = `${
        currentVariant.headline
      }\n\n${currentVariant.body.join("")}\n\n${currentVariant.cta}`

      /*
      await axiosInstance.post("/ai", {
        storeId: localStorage.getItem("storeId") || 0,
        info: fullTextContent,
        hashtag: currentVariant.hashtags.join(","),
      })
        */
    } catch (error) {
      console.error("DB 저장에 실패했습니다:", error)
      alert("콘텐츠 저장 중 오류가 발생했습니다.")
    } finally {
      await handleNaverUpload()
      setIsUploading(false)
      alert("콘텐츠가 성공적으로 저장되었습니다!")
      setCreationResult(null)
      router.push("/")
    }
  }

  // 네이버 블로그 업로드 함수
  const handleNaverUpload = async () => {
    if (!creationResult || !currentVariant) {
      alert("업로드할 콘텐츠가 없습니다.")
      return
    }

    try {
      /*
      await axiosInstance.post("/api/naver/blog/upload", {
        storeId: localStorage.getItem("storeId") || 0,
        title: currentVariant.headline,
        content: currentVariant.originalBody,
      })
        */

      alert("네이버 블로그에 성공적으로 업로드되었습니다!")
    } catch (error) {
      console.error("네이버 블로그 업로드 실패:", error)
      alert("네이버 블로그 업로드 중 오류가 발생했습니다.")
    } finally {
      setIsUploading(false)
    }
  }

  if (!creationResult || !currentVariant) {
    return <Typography>콘텐츠를 먼저 제작해주세요...</Typography>
  }

  return (
    <Container maxWidth="sm" sx={{ p: 0, pb: 7 }}>
      <UserProfileHeader />
      <Divider />

      <Box sx={{ p: 2 }}>
        <IconButton onClick={() => router.back()} sx={{ mb: 1 }}>
          <ArrowBackIcon />
        </IconButton>

        {/* AI 생성 콘텐츠 */}
        <Paper
          elevation={0}
          sx={{ border: "1px solid #e0e0e0", borderRadius: 2, p: 2, mb: 2 }}
        >
          <Typography
            variant="h5"
            component="h2"
            fontWeight="bold"
            sx={{ mt: 2, mb: 1 }}
          >
            {currentVariant.headline}
          </Typography>

          {currentVariant.body.map((item, index) =>
            item.startsWith("http") ? (
              <img
                key={item + index}
                src={item}
                style={{
                  width: "100%",
                  borderRadius: "4px",
                  objectFit: "cover",
                  margin: "16px 0",
                }}
                alt="본문 이미지"
              />
            ) : (
              <span key={item + index}>{item.replaceAll("\\n", "")}</span>
            )
          )}
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ whiteSpace: "pre-wrap", mt: 2 }}
          >
            {currentVariant.cta}
          </Typography>
        </Paper>

        {/* AI 생성 해시태그 */}
        <Stack
          direction="row"
          spacing={1}
          sx={{ mb: 2, flexWrap: "wrap", gap: 1 }}
        >
          {currentVariant.hashtags.map((tag) => (
            <Chip
              key={tag}
              label={tag}
              onDelete={() => handleHashtagDelete(tag)}
            />
          ))}
        </Stack>

        {/* 하단 버튼 영역 */}
        <Stack direction="row" spacing={2} alignItems="center">
          {/* '이전/다음' 버튼 */}
          <Paper
            variant="outlined"
            sx={{
              display: "flex",
              alignItems: "center",
              borderRadius: "8px",
              minWidth: 180,
              px: 2,
            }}
          >
            <IconButton
              onClick={handlePrevResult}
              disabled={currentIndex === 0}
              size="large"
            >
              <NavigateBeforeIcon />
            </IconButton>
            <Typography variant="body2" sx={{ px: 1 }}>
              {currentIndex + 1} / {creationResult.variants.length}
            </Typography>
            <IconButton
              onClick={handleNextResult}
              disabled={currentIndex >= creationResult.variants.length - 1}
            >
              <NavigateNextIcon />
            </IconButton>
          </Paper>

          <Button
            variant="contained"
            color="primary"
            fullWidth
            onClick={handleUpload}
            disabled={isUploading}
            sx={{ minWidth: 100, px: 2 }}
          >
            {isUploading ? <CircularProgress size={24} /> : "업로드"}
          </Button>
        </Stack>
      </Box>
    </Container>
  )
}

export default CreateResultPage
