import React, { useState, useEffect, useRef } from 'react';
import { ChatService } from '../services/api'; // 백엔드와 통신하기 위한 API 서비스입니다.

// 파일 하나의 정보를 담는 데이터 구조(타입)를 정의합니다.
interface RagFile {
  file_id: string; // 파일의 고유 아이디
  filename: string; // 파일 이름 (예: manual.pdf)
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'ERROR'; // 서버에서 처리 중인 상태
  is_active: boolean; // 이 파일을 실제 채팅 답변에 사용할지 여부
  created_at: string; // 업로드된 시간
}

/**
 * [지식 베이스(RAG) 관리 페이지]
 * 사용자가 문서를 업로드하고, 서버에서 분석 중인 상태를 확인하며, 
 * 어떤 문서를 챗봇이 참고하게 할지 결정하는 화면입니다.
 */
export const RagManager: React.FC = () => {
  // --- 상태 관리 (State) ---
  const [files, setFiles] = useState<RagFile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isPolling, setIsPolling] = useState(true); // PROCESSING 파일이 있는 동안만 true
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 1. 서버에서 파일 목록을 가져오는 함수
  const fetchFiles = async () => {
    try {
      const data = await ChatService.getRagFiles();
      setFiles(data);
      // PROCESSING 상태의 파일이 없으면 폴링을 스스로 멈춥니다.
      const hasProcessing = data.some((f: any) => f.status === 'PROCESSING' || f.status === 'PENDING');
      setIsPolling(hasProcessing);
    } catch (error) {
      console.error('Failed to fetch files:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 2. 파일 목록 폴링 제어
  // PROCESSING/PENDING 상태 파일이 있을 때만 5초 간격으로 목록을 새로고침합니다.
  // 모든 파일이 완료/에러 상태가 되면 폴링을 자동으로 멈춥니다.
  useEffect(() => {
    fetchFiles(); // 즉시 목록을 불러옴.
    if (!isPolling) return; // 폴링이 필요 없으면 인터벌 생성 안 함.

    const interval = setInterval(fetchFiles, 5000);
    return () => clearInterval(interval);
  }, [isPolling]); // isPolling이 바뀌면 인터벌을 재설정합니다.

  // 3. 파일 업로드 버튼을 눌렀을 때 실행되는 함수
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]; // 선택한 파일을 가져옵니다.
    if (!file) return;

    setIsUploading(true); // 업로드 시작! (버튼을 '업로드 중...'으로 바꿉니다)
    try {
      await ChatService.uploadRagFile(file);
      setIsPolling(true); // 새 파일이 업로드되면 폴링을 다시 시작합니다.
      await fetchFiles();
    } catch (error) {
      alert('업로드 실패: ' + error);
    } finally {
      setIsUploading(false); // 업로드 끝!
      if (fileInputRef.current) fileInputRef.current.value = ''; // 선택창을 초기화합니다.
    }
  };

  // 4. '채팅 사용' 스위치를 껐다 켰다 할 때 실행되는 함수
  const handleToggle = async (fileId: string, currentStatus: boolean) => {
    try {
      await ChatService.toggleRagFile(fileId, !currentStatus); // 서버에 상태 변경을 알립니다.
      // 화면에서도 즉시 상태를 바꿉니다 (새로고침 없이 사용자에게 바로 보여주기 위함).
      setFiles(prev => prev.map(f => f.file_id === fileId ? { ...f, is_active: !currentStatus } : f));
    } catch (error) {
      alert('상태 변경 실패');
    }
  };

  // 5. 삭제 버튼을 눌렀을 때 실행되는 함수
  const handleDelete = async (fileId: string) => {
    if (!confirm('정말로 이 파일을 삭제하시겠습니까? 관련 데이터가 모두 삭제됩니다.')) return;

    try {
      await ChatService.deleteRagFile(fileId); // 서버에서 삭제합니다.
      setFiles(prev => prev.filter(f => f.file_id !== fileId)); // 화면 목록에서 제거합니다.
    } catch (error) {
      alert('삭제 실패');
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 p-6 font-sans min-h-[500px]">
      <div className="max-w-5xl mx-auto w-full">

        {/* 상단 헤더 영역: 제목과 업로드 버튼 */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">지식 베이스(RAG) 관리</h1>
            <p className="text-slate-500 mt-1">챗봇이 학습할 문서를 업로드하고 관리하세요.</p>
          </div>

          {/* 업로드 버튼 (실제 파일 창은 숨겨두고 이 버튼이 클릭을 대신 전달합니다) */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className={`flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors shadow-sm disabled:opacity-50 cursor-pointer text-sm font-medium`}
          >
            {isUploading ? (
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
              </svg>
            )}
            {isUploading ? '업로드 중...' : '문서 업로드 (PDF, TXT)'}
          </button>

          {/* 실제로 파일을 받는 숨겨진 input 태그 */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleUpload}
            className="hidden"
            accept=".pdf,.txt"
          />
        </div>

        {/* 안내 문구 영역 */}
        <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-4 mb-6 flex gap-3 items-start">
          <svg className="w-5 h-5 text-indigo-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <div className="text-sm text-indigo-800">
            <strong>팁:</strong> 업로드된 문서 조각들은 벡터 DB에 저장됩니다.
            '채팅 사용' 스위치가 켜진 도큐먼트들만 챗봇 검색 대상에 포함됩니다.
          </div>
        </div>

        {/* 파일 목록 테이블 */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">파일명</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">처리 상태</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">업로드 일시</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">채팅 사용</th>
                <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">관리</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {/* 목록이 비어있을 때 보여줄 화면 */}
              {files.length === 0 && !isLoading && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-slate-400">
                    등록된 문서가 없습니다. 새로운 문서를 업로드해 주세요.
                  </td>
                </tr>
              )}
              {/* 목록을 하나씩 돌면서(map) 행(tr)을 만듭니다. */}
              {files.map(file => (
                <tr key={file.file_id} className="hover:bg-slate-50/50 transition-colors">
                  {/* 1. 파일명과 아이콘 */}
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded ${file.filename.endsWith('.pdf') ? 'bg-red-50 text-red-600' : 'bg-blue-50 text-blue-600'}`}>
                        {file.filename.endsWith('.pdf') ? (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
                        ) : (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                        )}
                      </div>
                      <span className="font-medium text-slate-700 truncate max-w-[200px]" title={file.filename}>
                        {file.filename}
                      </span>
                    </div>
                  </td>
                  {/* 2. 상태 뱃지 (대기/처리중/완료/에러) */}
                  <td className="px-6 py-4">
                    <StatusBadge status={file.status} />
                  </td>
                  {/* 3. 업로드 시간 */}
                  <td className="px-6 py-4 text-sm text-slate-500">
                    {new Date(file.created_at).toLocaleDateString()} {new Date(file.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </td>
                  {/* 4. 채팅 사용 스위치 */}
                  <td className="px-6 py-4">
                    <button
                      onClick={() => handleToggle(file.file_id, file.is_active)}
                      disabled={file.status !== 'COMPLETED'} // 분석이 완료된 파일만 켜고 끌 수 있습니다.
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${file.is_active ? 'bg-indigo-600' : 'bg-slate-200'} ${file.status !== 'COMPLETED' ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                    >
                      <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${file.is_active ? 'translate-x-6' : 'translate-x-1'}`} />
                    </button>
                  </td>
                  {/* 5. 삭제 버튼 */}
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => handleDelete(file.file_id)}
                      className="text-slate-400 hover:text-red-600 transition-colors p-2"
                      title="삭제"
                    >
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

/**
 * [상태 표시 뱃지 컴포넌트]
 * 파일 처리 상태에 따라 다른 색상과 텍스트를 보여줍니다.
 */
const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const configs: any = {
    'PENDING': { color: 'bg-slate-100 text-slate-600', text: '대기 중' },
    'PROCESSING': { color: 'bg-amber-50 text-amber-600 border border-amber-100', text: '처리 중...', animate: true },
    'COMPLETED': { color: 'bg-emerald-50 text-emerald-600 border border-emerald-100', text: '완료' },
    'ERROR': { color: 'bg-rose-50 text-rose-600 border border-rose-100', text: '에러' },
  };

  const config = configs[status] || configs['PENDING'];

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${config.color}`}>
      {/* '처리 중'일 때만 깜빡이는 효과를 줍니다. */}
      {config.animate && <span className="w-1.5 h-1.5 bg-amber-500 rounded-full animate-pulse" />}
      {config.text}
    </span>
  );
};
