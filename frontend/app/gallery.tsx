import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  Image,
  Alert,
  Modal,
  ActivityIndicator,
  TextInput,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import * as Constants from 'expo-constants';

const EXPO_PUBLIC_BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface GalleryPhoto {
  photoId: string;
  employeeId: string;
  imageBase64: string;
  eventVersion: string;
  uploadTimestamp: string;
}

export default function Gallery() {
  const params = useLocalSearchParams();
  const { employeeId } = params;

  const [currentEvent, setCurrentEvent] = useState('PM Connect 3.0');
  const [photos, setPhotos] = useState<GalleryPhoto[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [imageModalVisible, setImageModalVisible] = useState(false);

  const eventVersions = ['PM Connect 1.0', 'PM Connect 2.0', 'PM Connect 3.0'];

  useEffect(() => {
    fetchPhotos();
  }, [currentEvent]);

  const fetchPhotos = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/gallery/${encodeURIComponent(currentEvent)}`);
      if (response.ok) {
        const data = await response.json();
        setPhotos(data);
      } else {
        console.error('Failed to fetch photos');
      }
    } catch (error) {
      console.error('Error fetching photos:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkPermissions = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission Required', 'Please grant camera roll permissions to upload photos.');
      return false;
    }
    return true;
  };

  const pickImage = async () => {
    const hasPermission = await checkPermissions();
    if (!hasPermission) return;

    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
        base64: true,
      });

      if (!result.canceled && result.assets[0]) {
        const asset = result.assets[0];
        if (asset.base64) {
          await uploadImage(asset.base64);
        }
      }
    } catch (error) {
      console.error('Error picking image:', error);
      Alert.alert('Error', 'Failed to pick image');
    }
  };

  const uploadImage = async (base64Image: string) => {
    if (currentEvent !== 'PM Connect 3.0') {
      Alert.alert('Upload Restricted', 'You can only upload photos to PM Connect 3.0 gallery');
      return;
    }

    // Check current upload count for this user
    const userPhotos = photos.filter(photo => photo.employeeId === employeeId);
    if (userPhotos.length >= 2) {
      Alert.alert('Upload Limit', 'You can only upload maximum 2 photos to PM Connect 3.0');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('employeeId', employeeId as string);
      formData.append('eventVersion', currentEvent);
      
      // Create a blob from base64
      const blob = await (await fetch(`data:image/jpeg;base64,${base64Image}`)).blob();
      formData.append('file', blob as any, 'image.jpg');

      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/gallery/upload`, {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.ok) {
        Alert.alert('Success', 'Photo uploaded successfully!');
        fetchPhotos(); // Refresh the gallery
        setUploadModalVisible(false);
      } else {
        const errorData = await response.json();
        Alert.alert('Upload Failed', errorData.detail || 'Failed to upload photo');
      }
    } catch (error) {
      console.error('Error uploading image:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const openImageModal = (imageBase64: string) => {
    setSelectedImage(imageBase64);
    setImageModalVisible(true);
  };

  const renderPhotoGrid = () => {
    if (loading) {
      return (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#dc3545" />
          <Text style={styles.loadingText}>Loading photos...</Text>
        </View>
      );
    }

    if (photos.length === 0) {
      return (
        <View style={styles.noPhotosContainer}>
          <Text style={styles.noPhotosText}>📸 No photos yet</Text>
          <Text style={styles.noPhotosSubtext}>
            {currentEvent === 'PM Connect 3.0' 
              ? 'Be the first to upload a photo!'
              : 'Photos from this event will appear here'}
          </Text>
        </View>
      );
    }

    return (
      <View style={styles.photoGrid}>
        {photos.map((photo, index) => (
          <TouchableOpacity
            key={photo.photoId}
            style={styles.photoContainer}
            onPress={() => openImageModal(photo.imageBase64)}
          >
            <Image
              source={{ uri: `data:image/jpeg;base64,${photo.imageBase64}` }}
              style={styles.photo}
              resizeMode="cover"
            />
            <View style={styles.photoOverlay}>
              <Text style={styles.photoTimestamp}>
                {new Date(photo.uploadTimestamp).toLocaleDateString()}
              </Text>
            </View>
          </TouchableOpacity>
        ))}
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView style={styles.scrollView}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Text style={styles.backButtonText}>← Back</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Event Gallery</Text>
        </View>

        {/* Event Version Tabs */}
        <View style={styles.tabContainer}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tabScrollView}>
            {eventVersions.map((version) => (
              <TouchableOpacity
                key={version}
                style={[
                  styles.eventTab,
                  currentEvent === version && styles.activeEventTab,
                ]}
                onPress={() => setCurrentEvent(version)}
              >
                <Text
                  style={[
                    styles.eventTabText,
                    currentEvent === version && styles.activeEventTabText,
                  ]}
                >
                  {version}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Upload Button (only for PM Connect 3.0) */}
        {currentEvent === 'PM Connect 3.0' && (
          <View style={styles.uploadSection}>
            <TouchableOpacity
              style={styles.uploadButton}
              onPress={pickImage}
              disabled={uploading}
            >
              <Text style={styles.uploadButtonText}>
                {uploading ? '📸 Uploading...' : '📸 Upload Photo'}
              </Text>
            </TouchableOpacity>
            <Text style={styles.uploadHint}>
              You can upload up to 2 photos for PM Connect 3.0
            </Text>
          </View>
        )}

        {/* Photo Grid */}
        <View style={styles.galleryContent}>
          <Text style={styles.galleryTitle}>
            📸 {currentEvent} Gallery ({photos.length} photos)
          </Text>
          {renderPhotoGrid()}
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>© 2025 Jakson Limited. Powered by AI.</Text>
        </View>
      </ScrollView>

      {/* Image Modal */}
      <Modal
        visible={imageModalVisible}
        animationType="fade"
        transparent
        onRequestClose={() => setImageModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <TouchableOpacity
            style={styles.modalCloseArea}
            onPress={() => setImageModalVisible(false)}
          >
            <View style={styles.modalContent}>
              <TouchableOpacity
                style={styles.modalCloseButton}
                onPress={() => setImageModalVisible(false)}
              >
                <Text style={styles.modalCloseText}>✕</Text>
              </TouchableOpacity>
              {selectedImage && (
                <Image
                  source={{ uri: `data:image/jpeg;base64,${selectedImage}` }}
                  style={styles.modalImage}
                  resizeMode="contain"
                />
              )}
            </View>
          </TouchableOpacity>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    backgroundColor: '#dc3545',
    padding: 24,
    flexDirection: 'row',
    alignItems: 'center',
  },
  backButton: {
    marginRight: 16,
  },
  backButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  headerTitle: {
    color: 'white',
    fontSize: 20,
    fontWeight: 'bold',
  },
  tabContainer: {
    backgroundColor: 'white',
    paddingVertical: 16,
    marginBottom: 16,
  },
  tabScrollView: {
    paddingHorizontal: 16,
  },
  eventTab: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    marginRight: 12,
    borderRadius: 25,
    backgroundColor: '#f8f9fa',
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  activeEventTab: {
    backgroundColor: '#dc3545',
    borderColor: '#dc3545',
  },
  eventTabText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6c757d',
  },
  activeEventTabText: {
    color: 'white',
  },
  uploadSection: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
    alignItems: 'center',
  },
  uploadButton: {
    backgroundColor: '#28a745',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  uploadButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  uploadHint: {
    fontSize: 14,
    color: '#6c757d',
    textAlign: 'center',
  },
  galleryContent: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  galleryTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 16,
  },
  loadingContainer: {
    alignItems: 'center',
    padding: 32,
  },
  loadingText: {
    fontSize: 16,
    color: '#6c757d',
    marginTop: 16,
  },
  noPhotosContainer: {
    alignItems: 'center',
    padding: 32,
  },
  noPhotosText: {
    fontSize: 18,
    color: '#6c757d',
    marginBottom: 8,
  },
  noPhotosSubtext: {
    fontSize: 14,
    color: '#adb5bd',
    textAlign: 'center',
  },
  photoGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  photoContainer: {
    width: '48%',
    aspectRatio: 1,
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: '#f8f9fa',
    position: 'relative',
  },
  photo: {
    width: '100%',
    height: '100%',
  },
  photoOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    padding: 8,
  },
  photoTimestamp: {
    color: 'white',
    fontSize: 12,
    textAlign: 'center',
  },
  footer: {
    padding: 24,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 14,
    color: '#adb5bd',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalCloseArea: {
    flex: 1,
    width: '100%',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    width: '90%',
    height: '80%',
    position: 'relative',
  },
  modalCloseButton: {
    position: 'absolute',
    top: -50,
    right: 0,
    zIndex: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 20,
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalCloseText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  modalImage: {
    width: '100%',
    height: '100%',
  },
});