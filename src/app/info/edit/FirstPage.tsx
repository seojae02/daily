"use client"

import {
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
} from "@mui/material"
import { useEffect, useState } from "react"
import useStoreEdit from "./useStoreEdit"

export default function FirstInfoPage() {
  const [category, setCategory] = useState("")
  const { storeInfo, setStoreInfo } = useStoreEdit()

  useEffect(() => {
    setStoreInfo((prev) => ({ ...prev, type: category }))
  }, [category])

  return (
    <Stack width="100%" height="100%" alignItems="center">
      <Stack textAlign="center">1. 기본 가게 정보를 등록해주세요.</Stack>

      <Stack gap="24px" width="100%" maxWidth="400px" mt="24px" padding="12px">
        <TextField
          label="가게 이름"
          fullWidth
          size="small"
          value={storeInfo.name}
          onChange={(e) => setStoreInfo({ ...storeInfo, name: e.target.value })}
        />
        <FormControl fullWidth size="small">
          <InputLabel id="category-select-label">업종</InputLabel>
          <Select
            label="업종"
            value={category}
            labelId="category-select-label"
            onChange={(e) => setCategory(e.target.value as string)}
          >
            <MenuItem value="cafe">카페</MenuItem>
            <MenuItem value="restoran">음식점</MenuItem>
          </Select>
        </FormControl>
        <TextField
          label="가게 위치"
          fullWidth
          size="small"
          onChange={(e) => {
            setStoreInfo({
              ...storeInfo,
              location: e.target.value,
            })
          }}
          value={storeInfo.location}
          placeholder="예시: 서울시 강남구 역삼동 123-45"
        />
        <TextField
          label="가계 설명"
          fullWidth
          multiline
          rows={4}
          onChange={(e) => {
            setStoreInfo({
              ...storeInfo,
              description: e.target.value,
            })
          }}
          size="small"
          value={storeInfo.description}
          placeholder="예시: 02-123-4567"
        />
      </Stack>
    </Stack>
  )
}
