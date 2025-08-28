import { Box, Container, Divider } from "@mui/material"
import UserProfileHeader from "./components/UserProfileHeader"
import UploadHistory from "./components/UploadHistory"
import UploadPostCard from "./components/UploadPostCard"
import MainBottomNav from "./components/MainBottomNav"

export default function Home() {
  return (
    <Container maxWidth="sm" sx={{ p: 0, pb: 7 }}>
      <Box>
        <UserProfileHeader />
        <Divider />
        <UploadPostCard />
      </Box>
    </Container>
  )
}
