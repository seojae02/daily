'use client';
import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#556cd6', // 남색 계열
    },
    secondary: {
      main: '#19857b', // 초록색 계열
    },
    error: {
      main: '#red',
    },
  },
});

export default theme;