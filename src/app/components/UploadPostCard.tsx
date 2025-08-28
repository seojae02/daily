'use client';

import React from 'react';
import { Box, Typography, Card, CardMedia, Stack } from '@mui/material';
import FavoriteBorderIcon from '@mui/icons-material/FavoriteBorder';
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline';

// 임시 데이터 사용
const latestPostData = {
  id: 1,
  imageUrl: 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?q=80&w=1974&auto=format&fit=crop',
  likes: 128,
  comments: 15,
  content: `여름 신메뉴 출시!
시원하고 달콤한 망고가 듬뿍 올라간 "리얼 망고 빙수"
#망고빙수 #여름신메뉴`
};

function UploadPostCard() {
  return (
    <Box sx={{ p: 2 }}>
      
      <Typography variant="h6" gutterBottom fontWeight="bold">
        오늘의 업로드 내용!
      </Typography>

      {/* 이미지 카드 */}
      <Card sx={{ borderRadius: 3, boxShadow: 3, mb: 2 }}>
        <CardMedia
          component="img"
          height="220"
          image={latestPostData.imageUrl}
          alt="최근 포스트 이미지"
        />
        {/* 카드 하단 정보 */}
        <Box sx={{ p: 2 }}>
          {/* 좋아요, 댓글 수 */}
          <Stack direction="row" spacing={2}>
            <Stack direction="row" alignItems="center" spacing={0.5}>
              <FavoriteBorderIcon sx={{ fontSize: '1.2rem' }} color="action" />
              <Typography variant="body2" fontWeight="bold">{latestPostData.likes}</Typography>
            </Stack>
            <Stack direction="row" alignItems="center" spacing={0.5}>
              <ChatBubbleOutlineIcon sx={{ fontSize: '1.2rem' }} color="action" />
              <Typography variant="body2" fontWeight="bold">{latestPostData.comments}</Typography>
            </Stack>
          </Stack>
        </Box>
      </Card>
      {/* 피드 내용 */}
      <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
        {latestPostData.content}
      </Typography>
      
    </Box>
  );
}

export default UploadPostCard;