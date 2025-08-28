"use client"

import { useAtomValue } from "jotai"
import { Stack, TextField } from "@mui/material"
import { StoreIdAtom } from "@/app/atom/storeId"
import useStoreEdit from "./useStoreEdit"

export default function ThirdInfoPage() {
  const storeId = useAtomValue(StoreIdAtom)
  const {
    storeSnsInfo: { snsId: naverId, password: naverPw },
    setStoreSnsInfo,
  } = useStoreEdit()

  return (
    <Stack width="100%" height="100%" alignItems="center">
      <Stack textAlign="center">3. 사용 중인 SNS를 등록해주세요.</Stack>

      <Stack gap="24px" width="100%" maxWidth="400px" mt="24px" padding="12px">
        <TextField
          value={naverId}
          onChange={(e) =>
            setStoreSnsInfo((prev) => ({ ...prev, snsId: e.target.value }))
          }
          label="네이버 블로그 아이디"
        />
        <TextField
          value={naverPw}
          onChange={(e) =>
            setStoreSnsInfo((prev) => ({ ...prev, password: e.target.value }))
          }
          label="네이버 블로그 비밀번호"
          type="password"
        />
      </Stack>
    </Stack>
  )
}
