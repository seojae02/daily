"use client"

import React, { useEffect } from "react"
import {
  Box,
  Container,
  Typography,
  Button,
  Divider,
  Paper,
} from "@mui/material"
import UserProfileHeader from "../components/UserProfileHeader"
import { useRouter } from "next/navigation"
import { useInfo } from "./useInfo"

function StoreInfoPage() {
  const { push } = useRouter()
  const { storeInfo, fetchStoreInfo, contentFeel, fetchContentFeel } = useInfo()

  function handleEditClick() {
    push("/info/edit")
  }

  useEffect(() => {
    fetchStoreInfo()
    fetchContentFeel()
  }, [])

  return (
    <Container maxWidth="sm" sx={{ p: 0, pb: 7 }}>
      <UserProfileHeader />

      <Divider />

      <Box sx={{ p: 2 }}>
        {/* 가게 정보 타이틀, 수정 버튼 */}
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            mb: 1,
          }}
        >
          <Typography variant="h6" fontWeight="bold">
            가게 정보
          </Typography>
          <Button
            color="inherit"
            variant="contained"
            onClick={handleEditClick}
            sx={{
              color: "black",
              backgroundColor: "#f0f0f0",
              boxShadow: "none",
            }}
          >
            수정
          </Button>
        </Box>

        {/* 가게 정보 상세 */}
        <Typography variant="body1" sx={{ whiteSpace: "pre-wrap", mb: 2 }}>
          <strong>이름:</strong> {storeInfo.name}
          <br />
          <strong>업종:</strong> {storeInfo.type}
          <br />
          <strong>위치:</strong> {storeInfo.location}
          <br />
          <strong>설명:</strong> {storeInfo.description}
        </Typography>

        <Divider sx={{ my: 2 }} />

        {/* AI 컨텐츠 느낌 조회 */}
        <Typography variant="h6" fontWeight="bold" sx={{ mb: 1 }}>
          AI 컨텐츠 느낌
        </Typography>
        <Typography variant="body2" sx={{ mb: 1 }}>
          <strong>사진 느낌:</strong> {contentFeel.picFeel || "-"}
          <br />
          <strong>게시글 느낌:</strong> {contentFeel.postFeel || "-"}
        </Typography>
      </Box>
    </Container>
  )
}

export default StoreInfoPage
