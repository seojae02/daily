"use client"

import { Stack, Box, Typography, IconButton, Button } from "@mui/material"
import aiAxios from "@/config/axios"
import { PhotoCamera, Add } from "@mui/icons-material"
import { useRef, useState } from "react"
import useStoreEdit from "./useStoreEdit"

interface ImageUploadBoxProps {
  index: number
  onImageSelect: (file: File, index: number) => void
  selectedImage?: string
}

function ImageUploadBox({
  index,
  onImageSelect,
  selectedImage,
}: ImageUploadBoxProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      onImageSelect(file, index)
    }
  }

  return (
    <Box
      onClick={handleClick}
      sx={{
        width: "100%",
        height: "120px",
        border: "2px dashed #E0E0E0",
        borderRadius: "12px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        transition: "all 0.3s ease",
        backgroundColor: selectedImage ? "transparent" : "#FAFAFA",
        backgroundImage: selectedImage ? `url(${selectedImage})` : "none",
        backgroundSize: "cover",
        backgroundPosition: "center",
        position: "relative",
        "&:hover": {
          borderColor: "#1976D2",
          backgroundColor: selectedImage ? "transparent" : "#F0F7FF",
          transform: "translateY(-2px)",
          boxShadow: "0 4px 12px rgba(25, 118, 210, 0.15)",
        },
      }}
    >
      {!selectedImage && (
        <>
          <IconButton
            sx={{
              backgroundColor: "#1976D2",
              color: "white",
              mb: 1,
              "&:hover": {
                backgroundColor: "#1565C0",
              },
            }}
          >
            <PhotoCamera />
          </IconButton>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ fontWeight: 500 }}
          >
            사진 추가
          </Typography>
        </>
      )}

      {selectedImage && (
        <Box
          sx={{
            position: "absolute",
            top: 8,
            right: 8,
            backgroundColor: "rgba(0,0,0,0.6)",
            borderRadius: "50%",
            p: 0.5,
          }}
        >
          <Add
            sx={{
              color: "white",
              fontSize: 20,
              transform: "rotate(45deg)",
            }}
          />
        </Box>
      )}

      <input
        type="file"
        accept="image/*"
        ref={fileInputRef}
        onChange={handleFileChange}
        style={{ display: "none" }}
      />
    </Box>
  )
}

export default function SecondInfoPage() {
  // 이미지 파일 저장
  const [insideFiles, setInsideFiles] = useState<(File | null)[]>([
    null,
    null,
    null,
  ])
  const [outsideFiles, setOutsideFiles] = useState<(File | null)[]>([
    null,
    null,
    null,
  ])
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [insideImages, setInsideImages] = useState<string[]>(["", "", ""])
  const [outsideImages, setOutsideImages] = useState<string[]>(["", "", ""])
  // useStoreEdit 훅 사용
  const { setStoreImages } = useStoreEdit()

  const handleInsideImageSelect = (file: File, index: number) => {
    const imageUrl = URL.createObjectURL(file)
    setInsideImages((prev) => {
      const newArr = [...prev]
      newArr[index] = imageUrl
      return newArr
    })
    setInsideFiles((prev) => {
      const newArr = [...prev]
      newArr[index] = file
      return newArr
    })
    // 내부/외부 파일 합쳐서 jotai atom에 저장
    const nextInsideFiles = [
      ...insideFiles.slice(0, index),
      file,
      ...insideFiles.slice(index + 1),
    ]
    const allFiles = [...nextInsideFiles, ...outsideFiles].filter(
      (f): f is File => !!f
    )
    setStoreImages(allFiles)
  }

  const handleOutsideImageSelect = (file: File, index: number) => {
    const imageUrl = URL.createObjectURL(file)
    setOutsideImages((prev) => {
      const newArr = [...prev]
      newArr[index] = imageUrl
      return newArr
    })
    setOutsideFiles((prev) => {
      const newArr = [...prev]
      newArr[index] = file
      return newArr
    })
    // 내부/외부 파일 합쳐서 jotai atom에 저장
    const nextOutsideFiles = [
      ...outsideFiles.slice(0, index),
      file,
      ...outsideFiles.slice(index + 1),
    ]
    const allFiles = [...insideFiles, ...nextOutsideFiles].filter(
      (f): f is File => !!f
    )
    setStoreImages(allFiles)
  }
  // 이미지 업로드 함수를 export하여 마지막 페이지에서 호출
  const uploadImages = async () => {
    setIsUploading(true)
    setUploadError(null)
    try {
      const formData = new FormData()
      ;[...insideFiles, ...outsideFiles].forEach((file) => {
        if (file) formData.append("images", file)
      })
      const res = await aiAxios.post("/v1/upload-store-images", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      if (res.status !== 200) throw new Error("이미지 업로드 실패")
      // 성공 처리 (예: 알림)
    } catch (err) {
    } finally {
      setIsUploading(false)
    }
  }

  // ...기존 코드...
  // 업로드 버튼 제거, 다음 단계에서 uploadImages를 호출
  return (
    <Stack width="100%" height="100%" alignItems="center">
      <Typography
        variant="h6"
        sx={{
          fontWeight: 600,
          color: "#333",
          textAlign: "center",
          mb: 2,
        }}
      >
        2. 관련 가게 사진들을 등록해주세요
      </Typography>

      <Typography
        px="12px"
        variant="body2"
        color="text.secondary"
        width="100%"
        sx={{
          textAlign: "left",
        }}
      >
        가게의 내부 사진
      </Typography>

      <Stack gap="16px" width="100%" maxWidth="400px" padding="12px">
        {[0, 1, 2].map((idx) => (
          <ImageUploadBox
            key={idx}
            index={idx}
            onImageSelect={handleInsideImageSelect}
            selectedImage={insideImages[idx]}
          />
        ))}
      </Stack>

      <Typography
        px="12px"
        variant="body2"
        color="text.secondary"
        width="100%"
        sx={{
          textAlign: "left",
        }}
      >
        가게의 외부 사진
      </Typography>

      <Stack gap="16px" width="100%" maxWidth="400px" padding="12px">
        {[0, 1, 2].map((idx) => (
          <ImageUploadBox
            key={idx}
            index={idx}
            onImageSelect={handleOutsideImageSelect}
            selectedImage={outsideImages[idx]}
          />
        ))}
      </Stack>
    </Stack>
  )
}
