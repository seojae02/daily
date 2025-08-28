"use client"

import React, { useState } from "react"
import {
  Box,
  Container,
  Typography,
  Button,
  Divider,
  Paper,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Switch,
  Avatar,
  IconButton,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from "@mui/material"
import {
  Edit as EditIcon,
  Notifications as NotificationsIcon,
  Security as SecurityIcon,
  Help as HelpIcon,
  Logout as LogoutIcon,
  Store as StoreIcon,
  Person as PersonIcon,
  ChevronRight as ChevronRightIcon,
  Camera as CameraIcon,
} from "@mui/icons-material"
import UserProfileHeader from "../components/UserProfileHeader"

// 임시 데이터
const mockUserData = {
  name: "홍길동",
  email: "hong@example.com",
  storeName: "Daily Alley 카페",
  address: "화성시 동탄대로 123",
  profileImageUrl: "https://i.pravatar.cc/150",
  notifications: {
    push: true,
    email: false,
    marketing: true,
  },
}

function UserSettingsPage() {
  const [notifications, setNotifications] = useState(mockUserData.notifications)
  const [editProfileOpen, setEditProfileOpen] = useState(false)
  const [editStoreOpen, setEditStoreOpen] = useState(false)
  const [profileData, setProfileData] = useState({
    name: mockUserData.name,
    email: mockUserData.email,
  })
  const [storeData, setStoreData] = useState({
    storeName: mockUserData.storeName,
    address: mockUserData.address,
  })

  const handleNotificationChange =
    (type: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
      setNotifications((prev) => ({
        ...prev,
        [type]: event.target.checked,
      }))
    }

  const handleProfileSave = () => {
    // TODO: API 호출로 프로필 업데이트
    console.log("Profile updated:", profileData)
    setEditProfileOpen(false)
  }

  const handleStoreSave = () => {
    // TODO: API 호출로 가게 정보 업데이트
    console.log("Store updated:", storeData)
    setEditStoreOpen(false)
  }

  const handleLogout = () => {
    // TODO: 로그아웃 로직
    console.log("Logout")
  }

  return (
    <Container maxWidth="sm" sx={{ p: 0, pb: 7 }}>
      {/* 프로필 섹션 */}
      <Paper
        elevation={0}
        sx={{ m: 2, p: 2, borderRadius: 2, border: "1px solid #e0e0e0" }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          <Box sx={{ position: "relative" }}>
            <Avatar
              src={mockUserData.profileImageUrl}
              sx={{ width: 60, height: 60 }}
            />
            <IconButton
              size="small"
              sx={{
                position: "absolute",
                bottom: -5,
                right: -5,
                backgroundColor: "primary.main",
                color: "white",
                "&:hover": { backgroundColor: "primary.dark" },
              }}
            >
              <CameraIcon fontSize="small" />
            </IconButton>
          </Box>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" fontWeight="bold">
              {mockUserData.name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {mockUserData.email}
            </Typography>
          </Box>
          <IconButton onClick={() => setEditProfileOpen(true)}>
            <EditIcon />
          </IconButton>
        </Box>
      </Paper>

      {/* 설정 메뉴 */}
      <Paper
        elevation={0}
        sx={{ m: 2, borderRadius: 2, border: "1px solid #e0e0e0" }}
      >
        <List sx={{ p: 0 }}>
          {/* 가게 정보 수정 */}
          <ListItemButton onClick={() => setEditStoreOpen(true)} sx={{ py: 2 }}>
            <ListItemIcon>
              <StoreIcon color="primary" />
            </ListItemIcon>
            <ListItemText
              primary="가게 정보 수정"
              secondary="가게명, 주소 등을 변경할 수 있습니다"
            />
            <ChevronRightIcon color="action" />
          </ListItemButton>

          <Divider />

          {/* 알림 설정 */}
          <ListItem sx={{ py: 2 }}>
            <ListItemIcon>
              <NotificationsIcon color="primary" />
            </ListItemIcon>
            <ListItemText primary="푸시 알림" />
            <Switch
              checked={notifications.push}
              onChange={handleNotificationChange("push")}
            />
          </ListItem>

          <ListItem sx={{ py: 2 }}>
            <ListItemIcon>
              <Box sx={{ width: 24 }} />
            </ListItemIcon>
            <ListItemText primary="이메일 알림" />
            <Switch
              checked={notifications.email}
              onChange={handleNotificationChange("email")}
            />
          </ListItem>

          <ListItem sx={{ py: 2 }}>
            <ListItemIcon>
              <Box sx={{ width: 24 }} />
            </ListItemIcon>
            <ListItemText primary="마케팅 알림" />
            <Switch
              checked={notifications.marketing}
              onChange={handleNotificationChange("marketing")}
            />
          </ListItem>

          <Divider />

          {/* 보안 */}
          <ListItemButton sx={{ py: 2 }}>
            <ListItemIcon>
              <SecurityIcon color="primary" />
            </ListItemIcon>
            <ListItemText
              primary="보안"
              secondary="비밀번호 변경, 로그인 기록"
            />
            <ChevronRightIcon color="action" />
          </ListItemButton>

          <Divider />

          {/* 도움말 */}
          <ListItemButton sx={{ py: 2 }}>
            <ListItemIcon>
              <HelpIcon color="primary" />
            </ListItemIcon>
            <ListItemText
              primary="도움말"
              secondary="자주 묻는 질문, 문의하기"
            />
            <ChevronRightIcon color="action" />
          </ListItemButton>
        </List>
      </Paper>

      {/* 로그아웃 */}
      <Box sx={{ mx: 2, mb: 2 }}>
        <Button
          fullWidth
          variant="outlined"
          color="error"
          startIcon={<LogoutIcon />}
          onClick={handleLogout}
          sx={{ py: 1.5 }}
        >
          로그아웃
        </Button>
      </Box>

      {/* 프로필 편집 다이얼로그 */}
      <Dialog
        open={editProfileOpen}
        onClose={() => setEditProfileOpen(false)}
        fullWidth
      >
        <DialogTitle>프로필 편집</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="이름"
            fullWidth
            variant="outlined"
            value={profileData.name}
            onChange={(e) =>
              setProfileData((prev) => ({ ...prev, name: e.target.value }))
            }
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="이메일"
            type="email"
            fullWidth
            variant="outlined"
            value={profileData.email}
            onChange={(e) =>
              setProfileData((prev) => ({ ...prev, email: e.target.value }))
            }
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditProfileOpen(false)}>취소</Button>
          <Button onClick={handleProfileSave} variant="contained">
            저장
          </Button>
        </DialogActions>
      </Dialog>

      {/* 가게 정보 편집 다이얼로그 */}
      <Dialog
        open={editStoreOpen}
        onClose={() => setEditStoreOpen(false)}
        fullWidth
      >
        <DialogTitle>가게 정보 편집</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="가게명"
            fullWidth
            variant="outlined"
            value={storeData.storeName}
            onChange={(e) =>
              setStoreData((prev) => ({ ...prev, storeName: e.target.value }))
            }
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="주소"
            fullWidth
            variant="outlined"
            value={storeData.address}
            onChange={(e) =>
              setStoreData((prev) => ({ ...prev, address: e.target.value }))
            }
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditStoreOpen(false)}>취소</Button>
          <Button onClick={handleStoreSave} variant="contained">
            저장
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  )
}

export default UserSettingsPage
