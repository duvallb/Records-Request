import React, { useState, useCallback, useContext } from 'react';
import { useDropzone } from 'react-dropzone';
import { AuthContext } from '../App';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { 
  Upload, 
  File, 
  Download, 
  X, 
  FileText, 
  Image, 
  FileArchive,
  Video,
  Music,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const FileManager = ({ requestId, files = [], onFilesUpdate, disabled = false }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const { API } = useContext(AuthContext);

  const getFileIcon = (filename, contentType) => {
    if (contentType?.startsWith('image/')) return <Image className="w-4 h-4" />;
    if (contentType?.startsWith('video/')) return <Video className="w-4 h-4" />;
    if (contentType?.startsWith('audio/')) return <Music className="w-4 h-4" />;
    if (contentType?.includes('pdf')) return <FileText className="w-4 h-4" />;
    if (contentType?.includes('zip') || contentType?.includes('rar')) return <FileArchive className="w-4 h-4" />;
    return <File className="w-4 h-4" />;
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const onDrop = useCallback(async (acceptedFiles) => {
    if (disabled) {
      toast.error('File uploads are disabled for this request');
      return;
    }

    setUploading(true);
    
    for (const file of acceptedFiles) {
      const fileId = Math.random().toString(36).substr(2, 9);
      setUploadProgress(prev => ({ ...prev, [fileId]: 0 }));

      try {
        const formData = new FormData();
        formData.append('file', file);

        await axios.post(`${API}/upload/${requestId}`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(prev => ({ ...prev, [fileId]: percentCompleted }));
          },
        });

        toast.success(`${file.name} uploaded successfully`);
        setUploadProgress(prev => {
          const newProgress = { ...prev };
          delete newProgress[fileId];
          return newProgress;
        });

      } catch (error) {
        toast.error(`Failed to upload ${file.name}`);
        setUploadProgress(prev => {
          const newProgress = { ...prev };
          delete newProgress[fileId];
          return newProgress;
        });
      }
    }

    setUploading(false);
    if (onFilesUpdate) {
      onFilesUpdate(); // Refresh files list
    }
  }, [API, requestId, disabled, onFilesUpdate]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    disabled: disabled || uploading,
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: true
  });

  const handleDownload = async (fileId, filename) => {
    try {
      const response = await axios.get(`${API}/download/${fileId}`, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success('File downloaded successfully');
    } catch (error) {
      toast.error('Failed to download file');
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      {!disabled && (
        <Card className="border-2 border-dashed">
          <CardContent className="p-6">
            <div
              {...getRootProps()}
              className={`text-center p-8 rounded-lg transition-all cursor-pointer ${
                isDragActive 
                  ? 'bg-blue-50 border-blue-300' 
                  : 'bg-slate-50 hover:bg-slate-100'
              } ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <input {...getInputProps()} />
              <Upload className="w-12 h-12 mx-auto mb-4 text-slate-400" />
              {isDragActive ? (
                <p className="text-blue-600 font-medium">Drop files here...</p>
              ) : (
                <div>
                  <p className="text-slate-600 font-medium mb-2">
                    Drop files here or click to upload
                  </p>
                  <p className="text-sm text-slate-500">
                    Maximum file size: 10MB. Multiple files supported.
                  </p>
                </div>
              )}
            </div>

            {/* Upload Progress */}
            {Object.keys(uploadProgress).length > 0 && (
              <div className="mt-4 space-y-2">
                {Object.entries(uploadProgress).map(([fileId, progress]) => (
                  <div key={fileId} className="flex items-center gap-3">
                    <div className="flex-1 bg-slate-200 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <span className="text-sm text-slate-600 w-12">{progress}%</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Files List */}
      {files && files.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Attached Files ({files.length})
            </CardTitle>
            <CardDescription>
              Documents and files related to this request
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {files.map((file) => (
                <div key={file.id} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border">
                  <div className="flex items-center gap-3 flex-1">
                    {getFileIcon(file.original_name, file.content_type)}
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-800 truncate">
                        {file.original_name}
                      </p>
                      <div className="flex items-center gap-4 text-sm text-slate-500">
                        <span>{formatFileSize(file.file_size)}</span>
                        <span>•</span>
                        <span>{new Date(file.uploaded_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDownload(file.id, file.original_name)}
                    className="ml-3"
                  >
                    <Download className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {(!files || files.length === 0) && disabled && (
        <Card>
          <CardContent className="p-8 text-center">
            <FileText className="w-12 h-12 mx-auto mb-3 text-slate-300" />
            <p className="text-slate-500">No files attached to this request</p>
          </CardContent>
        </Card>
      )}

      {/* File Upload Guidelines */}
      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          <strong>File Guidelines:</strong> Supported formats include PDF, images (JPG, PNG), 
          documents (DOC, DOCX), and archives (ZIP). Maximum file size is 10MB per file. 
          All uploads are securely stored and only accessible to authorized personnel.
        </AlertDescription>
      </Alert>
    </div>
  );
};

export default FileManager;