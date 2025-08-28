import axios from "@/config/axios"
import { atom, useAtom } from "jotai"
import { useRouter } from "next/navigation"
import { StoreIdAtom } from "../atom/storeId"
import { StoreInfo } from "./edit/useStoreEdit"
import { useCallback } from "react"

const StoreInfoAtom = atom<StoreInfo>({
  name: "",
  type: "",
  location: "",
  description: "",
})

// contentFeel atom을 파일 최상단에 선언
export const ContentFeelAtom = atom<{ picFeel: string; postFeel: string }>({
  picFeel: "",
  postFeel: "",
})

export function useInfo() {
  const { push } = useRouter()
  const [storeId, setStoreId] = useAtom(StoreIdAtom)
  const [storeInfo, setStoreInfo] = useAtom(StoreInfoAtom)
  const [contentFeel, setContentFeel] = useAtom(ContentFeelAtom)

  // storeId가 바뀔 때만 fetchContentFeel 실행
  const fetchContentFeel = useCallback(
    async (id?: number | string) => {
      const targetId = id || storeId || localStorage.getItem("storeId")
      if (!targetId) return
      try {
        const { data, status } = await axios.get(
          `/contents?storeId=${targetId}`
        )
        if (status === 200) setContentFeel(data)
      } catch (e) {
        // 에러 처리
      }
    },
    [storeId, setContentFeel]
  )

  async function fetchStoreInfo() {
    let foundStoreId: number | string | null = storeId
    if (!storeId) {
      foundStoreId = localStorage.getItem("storeId")
      if (!foundStoreId) {
        push("/info/edit")
        return
      }
      setStoreId(Number(foundStoreId))
    }

    if (storeInfo.name) {
      return
    }

    const { data, status } = await axios.get<{ url: StoreInfo }>(
      `/store?storeId=${foundStoreId}`
    )

    if (status === 200) {
      setStoreInfo(data.url)
    } else {
      alert("가게 정보를 불러오는 데 실패했습니다. 다시 시도해주세요.")
    }
  }

  return {
    storeInfo,
    fetchStoreInfo,
    contentFeel,
    fetchContentFeel,
  }
}
