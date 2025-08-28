"use client"

import React, { useEffect, useState } from "react"
import { Paper, BottomNavigation, BottomNavigationAction } from "@mui/material"
import HomeIcon from "@mui/icons-material/Home"
import EditCalendarIcon from "@mui/icons-material/EditCalendar"
import AddPhotoAlternateIcon from "@mui/icons-material/AddPhotoAlternate"
import StorefrontIcon from "@mui/icons-material/Storefront"
import PersonOutlineIcon from "@mui/icons-material/PersonOutline"
import { useRouter, usePathname } from "next/navigation"

enum NavMenu {
  Schedule, // 0
  Create, // 1
  Home, // 2
  Info, // 3
  User, // 4
}

const valueToPath: { [key in NavMenu]: string } = {
  [NavMenu.Schedule]: "/schedule",
  [NavMenu.Create]: "/create",
  [NavMenu.Home]: "/",
  [NavMenu.Info]: "/info",
  [NavMenu.User]: "/user",
}

function MainBottomNav() {
  const router = useRouter()
  const pathname = usePathname()
  // 초기값을 undefined로 설정하여 아무것도 선택되지 않은 상태로 시작
  const [value, setValue] = useState<NavMenu | undefined>(undefined)

  useEffect(() => {
    const matchingKey = Object.keys(valueToPath).find(
      (key) => valueToPath[Number(key) as NavMenu] === pathname
    )
    if (matchingKey) {
      setValue(Number(matchingKey) as NavMenu)
    } else {
      // 매칭되는 경로가 없으면 아무것도 선택하지 않음
      setValue(undefined)
    }
  }, [pathname])

  return (
    <Paper sx={{ zIndex: 1000 }} elevation={3}>
      {/* 하단 네비게이션 바 본체 */}
      <BottomNavigation
        showLabels
        value={value}
        onChange={(event, newValue: NavMenu) => {
          const path = valueToPath[newValue]
          if (path) {
            router.push(path)
          }
        }}
        sx={{
          "& .MuiBottomNavigationAction-root": {
            color: "#757575",
            transition: "all 0.3s ease",
            "&.Mui-selected": {
              color: "#556cd6",
              "& .MuiBottomNavigationAction-label": {
                fontSize: "0.75rem",
                fontWeight: "600",
              },
              "& .MuiSvgIcon-root": {
                fontSize: "1.5rem",
                transform: "scale(1.1)",
              },
            },
            "&:hover": {
              color: "#556cd6",
              backgroundColor: "rgba(85, 108, 214, 0.04)",
            },
          },
          "& .MuiBottomNavigationAction-label": {
            fontSize: "0.7rem",
            fontWeight: "500",
          },
        }}
      >
        <BottomNavigationAction label="일정 정리" icon={<EditCalendarIcon />} />
        <BottomNavigationAction
          label="콘텐츠 제작"
          icon={<AddPhotoAlternateIcon />}
        />
        <BottomNavigationAction label="메인화면" icon={<HomeIcon />} />
        <BottomNavigationAction label="가게 정보" icon={<StorefrontIcon />} />
        <BottomNavigationAction label="사용자" icon={<PersonOutlineIcon />} />
      </BottomNavigation>
    </Paper>
  )
}

export default MainBottomNav
