'use client';

import React from 'react';
import { Box, Typography, Stack, Avatar } from '@mui/material';

// 임시 데이터 배열
const historyData = [
  { id: 1, imageUrl: 'https://i.pravatar.cc/150?img=1' },
  { id: 2, imageUrl: 'https://i.pravatar.cc/150?img=2' },
  { id: 3, imageUrl: 'https://i.pravatar.cc/150?img=3' },
  { id: 4, imageUrl: 'https://i.pravatar.cc/150?img=4' },
  { id: 5, imageUrl: 'https://i.pravatar.cc/150?img=5' },
  { id: 6, imageUrl: 'https://i.pravatar.cc/150?img=6' },
  { id: 7, imageUrl: 'https://i.pravatar.cc/150?img=7' },
];

function UploadHistory() {
  return (
    <Box sx={{ py: 2, px: 2 }}>
      <Typography variant="h6" component="h2" sx={{ mb: 2, fontWeight: 'bold' }}>
        오늘의 업로드 내역!
      </Typography>
      <Stack 
        direction="row" 
        spacing={2}    
        
        sx={{ 
          overflowX: 'auto', 
          pb: 1, 
          '&::-webkit-scrollbar': {
            height: '4px',
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: 'rgba(0,0,0,.1)',
            borderRadius: '4px',
          }
        }}
      >
        {historyData.map((item) => (
          <Avatar
            key={item.id} 
            src={item.imageUrl}
            sx={{ 
              width: 64, 
              height: 64, 
              border: '2px solid #e0e0e0'
            }}
          />
        ))}
      </Stack>
    </Box>
  );
}

export default UploadHistory;