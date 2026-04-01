import { defineConfig } from 'vite'; // Vite 설정을 도와주는 함수를 가져옵니다.
import react from '@vitejs/plugin-react'; // Vite에서 React를 사용할 수 있게 해주는 플러그인입니다.
import tailwindcss from '@tailwindcss/vite'; // Tailwind CSS를 Vite에서 처리해주기 위한 플러그인입니다.

// https://vitejs.dev/config/ - 자세한 설정 정보는 여기에서 확인할 수 있습니다.
export default defineConfig({
  // 프로젝트에서 사용할 플러그인들을 나열합니다.
  plugins: [
    react(), // React 코드(JSX 등)를 해석하고 최적화합니다.
    tailwindcss() // CSS 파일에서 Tailwind 문법을 처리합니다.
  ],

  // 전역 변수를 정의합니다. 
  // 라이브러리 형태(lib)로 빌드할 때 일부 패키지가 process.env를 참조하여 에러가 나는 것을 방지하기 위해 빈 객체로 설정합니다.
  define: {
    'process.env': {},
  },

  // 빌드 관련 설정입니다. (npm run build 시 적용되는 옵션)
  build: {
    // 이 프로젝트를 일반 웹사이트가 아닌 '라이브러리(다른 곳에 끼워 쓰는 용도)'로 빌드하겠다는 설정입니다.
    lib: {
      entry: './src/main.tsx', // 빌드의 시작점이 되는 파일입니다.
      name: 'Chatbot',        // 라이브러리의 이름입니다.
      fileName: 'chatbot',    // 생성될 파일의 이름입니다. (예: chatbot.js)
      formats: ['es']         // 최신 자바스크립트 표준(ES Module) 형식으로 내보냅니다.
    },
    // 하단 도구인 Rollup에 직접 전달되는 세부 옵션입니다.
    rollupOptions: {
      output: {
        // 생성되는 자산(CSS 등)의 파일명 형식을 지정합니다.
        assetFileNames: 'assets/[name].[ext]'
      }
    }
  }
});

