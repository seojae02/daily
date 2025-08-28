import axios from "axios"

const AI_API_BASE_URL = "https://daily-alley-api.iubns.net:7100/"

const aiAxiosInstance = axios.create({
  baseURL: AI_API_BASE_URL,
  headers: {},
  // 응답 대시 시간 (30초)
  timeout: 120000,
})

export default aiAxiosInstance
