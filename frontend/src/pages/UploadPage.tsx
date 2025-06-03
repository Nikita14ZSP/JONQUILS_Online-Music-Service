import React, { useState } from 'react';
import axios from 'axios';

const UploadPage: React.FC = () => {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [message, setMessage] = useState<string>('');

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files) {
            setSelectedFile(event.target.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!selectedFile) {
            setMessage('Пожалуйста, выберите файл для загрузки.');
            return;
        }

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const response = await axios.post('http://localhost:8000/api/v1/upload/uploadfile/', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setMessage(response.data.info);
        } catch (error) {
            setMessage('Ошибка при загрузке файла.');
            console.error('Ошибка загрузки:', error);
        }
    };

    return (
        <div className="upload-page">
            <h1>Загрузка трека</h1>
            <input type="file" onChange={handleFileChange} accept="audio/mp3" />
            <button onClick={handleUpload} disabled={!selectedFile}>Загрузить</button>
            {message && <p>{message}</p>}
        </div>
    );
};

export default UploadPage; 