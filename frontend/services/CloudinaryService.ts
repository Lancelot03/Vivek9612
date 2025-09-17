import { Cloudinary } from '@cloudinary/url-gen';
import { upload, UploadApiOptions } from 'cloudinary-react-native';

interface CloudinaryConfig {
  cloudName: string;
  uploadPreset: string;
  folder?: string;
}

interface UploadResult {
  public_id: string;
  secure_url: string;
  width: number;
  height: number;
  format: string;
  bytes: number;
}

class CloudinaryService {
  private static instance: CloudinaryService;
  private cld: Cloudinary;
  private config: CloudinaryConfig;

  private constructor() {
    this.config = {
      cloudName: 'pm-connect-demo', // Default demo cloud name
      uploadPreset: 'pm_connect_preset',
      folder: 'pm_connect_app'
    };

    this.cld = new Cloudinary({
      cloud: {
        cloudName: this.config.cloudName
      },
      url: {
        secure: true
      }
    });
  }

  public static getInstance(): CloudinaryService {
    if (!CloudinaryService.instance) {
      CloudinaryService.instance = new CloudinaryService();
    }
    return CloudinaryService.instance;
  }

  public getCloudinary(): Cloudinary {
    return this.cld;
  }

  public async uploadImage(
    imageUri: string,
    folder?: string,
    tags?: string[]
  ): Promise<UploadResult> {
    try {
      const uploadOptions: UploadApiOptions = {
        upload_preset: this.config.uploadPreset,
        unsigned: true,
        folder: folder || this.config.folder,
        tags: tags || ['mobile_upload'],
        transformation: [
          { quality: 'auto:good' },
          { format: 'auto' }
        ]
      };

      return new Promise((resolve, reject) => {
        upload(this.cld, {
          file: imageUri,
          options: uploadOptions,
          callback: (error: any, response: any) => {
            if (error) {
              reject(error);
            } else {
              resolve({
                public_id: response.public_id,
                secure_url: response.secure_url,
                width: response.width,
                height: response.height,
                format: response.format,
                bytes: response.bytes
              });
            }
          }
        });
      });
    } catch (error) {
      throw new Error(`Upload failed: ${error}`);
    }
  }

  public generateImageUrl(
    publicId: string,
    width?: number,
    height?: number,
    crop: string = 'fill',
    quality: string = 'auto:good'
  ): string {
    const image = this.cld.image(publicId);
    
    if (width || height) {
      image.resize(`c_${crop}${width ? `,w_${width}` : ''}${height ? `,h_${height}` : ''}`);
    }
    
    image.quality(quality).format('auto');
    
    return image.toURL();
  }

  public generateVideoUrl(
    publicId: string,
    streamingProfile?: string
  ): string {
    const video = this.cld.video(publicId);
    
    if (streamingProfile) {
      video.format('m3u8');
      // Add streaming profile transformation
      video.addTransformation(`sp_${streamingProfile}`);
    }
    
    return video.toURL();
  }

  public generateThumbnailUrl(publicId: string, size: number = 300): string {
    return this.generateImageUrl(publicId, size, size, 'fill', 'auto:good');
  }

  public generateResponsiveUrls(publicId: string): {
    thumbnail: string;
    medium: string;
    large: string;
    full: string;
  } {
    return {
      thumbnail: this.generateImageUrl(publicId, 300, 300, 'fill'),
      medium: this.generateImageUrl(publicId, 800, 600, 'limit'),
      large: this.generateImageUrl(publicId, 1200, 900, 'limit'),
      full: this.generateImageUrl(publicId)
    };
  }
}

export default CloudinaryService;