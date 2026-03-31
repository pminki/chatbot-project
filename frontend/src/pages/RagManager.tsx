import React, { useState, useEffect, useRef } from 'react';
import { ChatService } from '../services/api';

interface RagFile {
  file_id: string;
  filename: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'ERROR';
  is_active: boolean;
  created_at: string;
}

export const RagManager: React.FC = () => {
  const [files, setFiles] = useState<RagFile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 1. 파일 목록 로드
  const fetchFiles = async () => {
    try {
      const data = await ChatService.getRagFiles();
      setFiles(data);
    } catch (error) {
      console.error('Failed to fetch files:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
    // 주기적으로 상태를 업데이트하기 위해 폴링 (Processing 중인 파일이 있을 때 유용)
    const interval = setInterval(fetchFiles, 5000);
    return () => clearInterval(interval);
  }, []);

  // 2. 파일 업로드 핸들러
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      await ChatService.uploadRagFile(file);
      await fetchFiles();
    } catch (error) {
      alert('업로드 실패: ' + error);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // 3. 상태 토글 핸들러
  const handleToggle = async (fileId: string, currentStatus: boolean) => {
    try {
      await ChatService.toggleRagFile(fileId, !currentStatus);
      setFiles(prev => prev.map(f => f.file_id === fileId ? { ...f, is_active: !currentStatus } : f));
    } catch (error) {
      alert('상태 변경 실패');
    }
  };

  // 4. 파일 삭제 핸들러
  const handleDelete = async (fileId: string) => {
    if (!confirm('정말로 이 파일을 삭제하시겠습니까? 관련 데이터가 모두 삭제됩니다.')) return;

    try {
      await ChatService.deleteRagFile(fileId);
      setFiles(prev => prev.filter(f => f.file_id !== fileId));
    } catch (error) {
      alert('삭제 실패');
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 p-6 font-sans min-h-[500px]">
      <div className="max-w-5xl mx-auto w-full">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">지식 베이스(RAG) 관리</h1>
            <p className="text-slate-500 mt-1">챗봇이 학습할 문서를 업로드하고 관리하세요.</p>
          </div>
          
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
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleUpload} 
            className="hidden" 
            accept=".pdf,.txt"
          />
        </div>

        {/* Info Alert */}
        <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-4 mb-6 flex gap-3 items-start">
          <svg className="w-5 h-5 text-indigo-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <div className="text-sm text-indigo-800">
            <strong>팁:</strong> 업로드된 문서 조각들은 벡터 DB에 저장됩니다. 
            '채팅 사용' 스위치가 켜진 도큐먼트들만 챗봇 검색 대상에 포함됩니다.
          </div>
        </div>

        {/* File Table */}
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
              {files.length === 0 && !isLoading && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-slate-400">
                    등록된 문서가 없습니다. 새로운 문서를 업로드해 주세요.
                  </td>
                </tr>
              )}
              {files.map(file => (
                <tr key={file.file_id} className="hover:bg-slate-50/50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded ${file.filename.endsWith('.pdf') ? 'bg-red-50 text-red-600' : 'bg-blue-50 text-blue-600'}`}>
                        {file.filename.endsWith('.pdf') ? (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/></svg>
                        ) : (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                        )}
                      </div>
                      <span className="font-medium text-slate-700 truncate max-w-[200px]" title={file.filename}>
                        {file.filename}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={file.status} />
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-500">
                    {new Date(file.created_at).toLocaleDateString()} {new Date(file.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td className="px-6 py-4">
                    <button 
                      onClick={() => handleToggle(file.file_id, file.is_active)}
                      disabled={file.status !== 'COMPLETED'}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${file.is_active ? 'bg-indigo-600' : 'bg-slate-200'} ${file.status !== 'COMPLETED' ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                    >
                      <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${file.is_active ? 'translate-x-6' : 'translate-x-1'}`} />
                    </button>
                  </td>
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
      {config.animate && <span className="w-1.5 h-1.5 bg-amber-500 rounded-full animate-pulse" />}
      {config.text}
    </span>
  );
};
