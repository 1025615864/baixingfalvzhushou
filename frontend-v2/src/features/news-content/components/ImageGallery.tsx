/**
 * Image Gallery Component
 * 图片库管理组件
 */

import { useState, memo } from 'react';
import { Card, Upload, Modal, Image as AntImage, Row, Col, Button, message } from 'antd';

import { useUploadImage, useDeleteImage } from '../hooks';
import type { UploadImageResponse } from '../types';

interface ImageGalleryProps {
  onSelect?: (image: UploadImageResponse) => void;
  multiple?: boolean;
}

export const ImageGallery = memo(function ImageGallery({ onSelect }: ImageGalleryProps) {
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewImage, setPreviewImage] = useState<string>('');
  const [images, setImages] = useState<UploadImageResponse[]>([]);

  const uploadImageMutation = useUploadImage();
  const deleteImageMutation = useDeleteImage();

  const handleUpload = (file: File) => {
    void uploadImageMutation.mutateAsync(file).then((result) => {
      setImages((prev) => [result, ...prev]);
      void message.success('上传成功');
    }).catch(() => {
      void message.error('上传失败');
    });
    return false;
  };

  const handleDelete = (id: string) => {
    void deleteImageMutation.mutateAsync(id).then(() => {
      setImages((prev) => prev.filter((img) => img.id !== id));
      void message.success('删除成功');
    }).catch(() => {
      void message.error('删除失败');
    });
  };

  const handlePreview = (url: string) => {
    setPreviewImage(url);
    setPreviewVisible(true);
  };

  const handleSelect = (image: UploadImageResponse) => {
    if (onSelect) {
      onSelect(image);
    }
  };

  return (
    <div className="image-gallery">
      <Card
        title="图片库"
        extra={
          <Upload beforeUpload={handleUpload} showUploadList={false}>
            <Button loading={uploadImageMutation.isPending}>
              上传图片
            </Button>
          </Upload>
        }
      >
        <Row gutter={[16, 16]}>
          {images.map((image) => (
            <Col key={image.id} xs={12} sm={8} md={6} lg={4}>
              <div className="image-item relative group">
                <AntImage.PreviewGroup>
                  <AntImage
                    src={image.thumbnailUrl || image.url}
                    alt={image.alt}
                    className="w-full h-32 object-cover rounded"
                    preview={false}
                  />
                </AntImage.PreviewGroup>
                <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2 rounded">
                  <Button
                    size="small"
                    onClick={() => handlePreview(image.url)}
                  />
                  <Button
                    size="small"
                    type="primary"
                    onClick={() => handleSelect(image)}
                  >
                    选用
                  </Button>
                  <Button
                    size="small"
                    danger
                    onClick={() => handleDelete(image.id)}
                  />
                </div>
              </div>
            </Col>
          ))}
        </Row>

        {images.length === 0 && (
          <div className="text-center py-8 text-gray-400">
            暂无图片，点击上传
          </div>
        )}
      </Card>

      <Modal
        open={previewVisible}
        footer={null}
        onCancel={() => setPreviewVisible(false)}
      >
        <img src={previewImage} alt="预览" className="w-full" />
      </Modal>
    </div>
  );
});
