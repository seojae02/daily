import axios from "@/config/axios"
import aiAxiosInstance from "@/config/aiAxiosInstance"
import { atom, useAtom, useSetAtom } from "jotai"

const StoreInfoAtom = atom<StoreInfo>({
  name: "",
  type: "",
  location: "",
  description: "",
})

// 컨텐츠 느낌 저장용 atom
const ContentFeelAtom = atom<ContentFeel>({
  storeId: 0,
  picFeel: "",
  postFeel: "",
})

export interface ContentFeel {
  storeId: number
  picFeel: string
  postFeel: string
}

const StoreSnsInfoAtom = atom<StoreSNSInfo>({
  storeId: 0,
  snsId: "",
  password: "",
  type: "NAVER",
})

const StoreImageAtom = atom<File[]>([])
export interface StoreInfo {
  name: string
  type: string
  location: string
  description: string
}

interface RegistrationResponse {
  message: string
  storeId: number
}

interface StoreSNSInfo {
  storeId: number
  snsId: string
  password: string
  type: "NAVER" | "INSTAGRAM"
}

export default function useStoreEdit() {
  const [storeInfo, setStoreInfo] = useAtom(StoreInfoAtom)
  const [storeSnsInfo, setStoreSnsInfo] = useAtom(StoreSnsInfoAtom)
  const [contentFeel, setContentFeel] = useAtom(ContentFeelAtom)
  const setStoreId = useSetAtom(atom<number | null>(null))
  const [storeImages, setStoreImages] = useAtom(StoreImageAtom)

  // 이미지 업로드 함수
  async function uploadStoreImages() {
    if (!storeImages || storeImages.length === 0) return null
    const storeId = localStorage.getItem("storeId")
    const formData = new FormData()
    storeImages.forEach((file) => {
      formData.append("images", file)
    })
    formData.append("storeId", storeId || "")
    const { status, data } = await aiAxiosInstance.post(
      "/v1/upload-store-images",
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      }
    )
    return { status, data }
  }

  async function saveContentFeel() {
    const { status } = await axios.post("/contents", {
      ...contentFeel,
      storeId: localStorage.getItem("storeId"),
    })
    return status
  }

  async function registrationStoreInfo() {
    const { data, status } = await axios.post<RegistrationResponse>(
      "/store",
      storeInfo
    )

    if (status === 200) {
      localStorage.setItem("storeId", String(data.storeId))
      setStoreId(data.storeId)
      setStoreSnsInfo((prev) => ({ ...prev, storeId: data.storeId }))
      setContentFeel((prev) => ({ ...prev, storeId: data.storeId }))
    }

    return {
      status,
    }
  }

  async function saveStoreSnsInfo() {
    const { status } = await axios.post("/sns", storeSnsInfo)
    return status
  }

  return {
    registrationStoreInfo,
    saveStoreSnsInfo,
    storeInfo,
    setStoreInfo,
    setStoreSnsInfo,
    storeSnsInfo,
    contentFeel,
    setContentFeel,
    saveContentFeel,
    storeImages,
    setStoreImages,
    uploadStoreImages,
  }
}
