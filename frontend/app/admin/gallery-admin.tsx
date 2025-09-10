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
  ActivityIndicator,
  Modal,
} from 'react-native';
import { router } from 'expo-router';
import * as Constants from 'expo-constants';

const EXPO_PUBLIC_BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface GalleryPhoto {
  photoId: string;
  employeeId: string;
  imageBase64: string;
  eventVersion: string;
  uploadTimestamp: string;
}

export default function AdminGallery() {
  const [currentEvent, setCurrentEvent] = useState('PM Connect 3.0');
  const [photos, setPhotos] = useState<GalleryPhoto[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [imageModalVisible, setImageModalVisible] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

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

  const handleDeletePhoto = (photoId: string) => {
    Alert.alert(
      'Delete Photo',
      'Are you sure you want to delete this photo? This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => deletePhoto(photoId),
        },
      ]
    );
  };

  const deletePhoto = async (photoId: string) => {
    setDeleting(photoId);
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/gallery/${photoId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        Alert.alert('Success', 'Photo deleted successfully');
        fetchPhotos(); // Refresh the gallery
      } else {
        Alert.alert('Delete Failed', 'Failed to delete photo');
      }
    } catch (error) {
      console.error('Error deleting photo:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setDeleting(null);
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
          <ActivityIndicator size="large" color="#007bff" />
          <Text style={styles.loadingText}>Loading photos...</Text>
        </View>
      );
    }

    if (photos.length === 0) {
      return (
        <View style={styles.noPhotosContainer}>
          <Text style={styles.noPhotosText}>📸 No photos yet</Text>
          <Text style={styles.noPhotosSubtext}>
            Photos uploaded by attendees will appear here
          </Text>
        </View>
      );
    }

    return (
      <View style={styles.photoGrid}>
        {photos.map((photo) => (
          <View key={photo.photoId} style={styles.photoContainer}>
            <TouchableOpacity
              style={styles.photoTouchable}
              onPress={() => openImageModal(photo.imageBase64)}
            >
              <Image
                source={{ uri: `data:image/jpeg;base64,${photo.imageBase64}` }}
                style={styles.photo}
                resizeMode="cover"
              />
              <View style={styles.photoOverlay}>
                <Text style={styles.photoEmployeeId}>ID: {photo.employeeId}</Text>
                <Text style={styles.photoTimestamp}>
                  {new Date(photo.uploadTimestamp).toLocaleDateString()}
                </Text>
              </View>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.deletePhotoButton}
              onPress={() => handleDeletePhoto(photo.photoId)}
              disabled={deleting === photo.photoId}
            >
              {deleting === photo.photoId ? (
                <ActivityIndicator size="small" color="white" />
              ) : (
                <Text style={styles.deletePhotoText}>🗑️</Text>
              )}
            </TouchableOpacity>
          </View>
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
          <Text style={styles.headerTitle}>Gallery Management</Text>
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

        {/* Statistics */}
        <View style={styles.statsSection}>
          <Text style={styles.sectionTitle}>📊 Gallery Statistics</Text>
          <View style={styles.statsGrid}>
            <View style={styles.statCard}>
              <Text style={styles.statNumber}>{photos.length}</Text>
              <Text style={styles.statLabel}>Total Photos</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statNumber}>
                {new Set(photos.map(p => p.employeeId)).size}
              </Text>
              <Text style={styles.statLabel}>Contributors</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statNumber}>
                {Math.round(photos.reduce((acc, photo) => acc + photo.imageBase64.length, 0) / 1024 / 1024 * 100) / 100}
              </Text>
              <Text style={styles.statLabel}>MB Storage</Text>
            </View>
          </View>
        </View>

        {/* Photo Gallery */}
        <View style={styles.galleryContent}>
          <View style={styles.galleryHeader}>
            <Text style={styles.galleryTitle}>
              📸 {currentEvent} Gallery ({photos.length} photos)
            </Text>
            <TouchableOpacity style={styles.refreshButton} onPress={fetchPhotos}>
              <Text style={styles.refreshButtonText}>🔄 Refresh</Text>
            </TouchableOpacity>
          </View>
          {renderPhotoGrid()}
        </View>

        {/* Management Notes */}
        <View style={styles.notesSection}>
          <Text style={styles.sectionTitle}>📝 Management Notes</Text>
          <View style={styles.notesList}>
            <Text style={styles.noteItem}>
              • Photos are automatically stored in base64 format for cross-platform compatibility
            </Text>
            <Text style={styles.noteItem}>
              • Users can upload maximum 2 photos for PM Connect 3.0
            </Text>
            <Text style={styles.noteItem}>
              • Delete inappropriate photos using the delete button on each photo
            </Text>
            <Text style={styles.noteItem}>
              • All photo uploads are logged with employee ID and timestamp
            </Text>
          </View>
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
    backgroundColor: '#007bff',
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
    backgroundColor: '#007bff',
    borderColor: '#007bff',
  },
  eventTabText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6c757d',
  },
  activeEventTabText: {
    color: 'white',
  },
  statsSection: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#f8f9fa',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  statNumber: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#007bff',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#6c757d',
    textAlign: 'center',
  },
  galleryContent: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  galleryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  galleryTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
    flex: 1,
  },
  refreshButton: {
    backgroundColor: '#007bff',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  refreshButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
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
    position: 'relative',
  },
  photoTouchable: {
    width: '100%',
    height: '100%',
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: '#f8f9fa',
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
  photoEmployeeId: {
    color: 'white',
    fontSize: 10,
    fontWeight: 'bold',
  },
  photoTimestamp: {
    color: 'white',
    fontSize: 10,
  },
  deletePhotoButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: 'rgba(220, 53, 69, 0.9)',
    borderRadius: 16,
    width: 32,
    height: 32,
    justifyContent: 'center',
    alignItems: 'center',
  },
  deletePhotoText: {
    fontSize: 16,
  },
  notesSection: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  notesList: {
    gap: 8,
  },
  noteItem: {
    fontSize: 14,
    color: '#6c757d',
    lineHeight: 20,
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