import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { router } from 'expo-router';
import * as DocumentPicker from 'expo-document-picker';
import * as Constants from 'expo-constants';

const EXPO_PUBLIC_BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

interface Agenda {
  agendaId: string;
  agendaTitle: string;
  pdfBase64: string;
  uploadTimestamp: string;
}

export default function AdminAgenda() {
  const [agenda, setAgenda] = useState<Agenda | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchCurrentAgenda();
  }, []);

  const fetchCurrentAgenda = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/agenda`);
      if (response.ok) {
        const data = await response.json();
        if (data.agendaId) {
          setAgenda(data);
        }
      } else {
        console.log('No agenda found');
      }
    } catch (error) {
      console.error('Error fetching agenda:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleUploadAgenda = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: 'application/pdf',
        copyToCacheDirectory: true,
      });

      if (!result.canceled && result.assets[0]) {
        const asset = result.assets[0];
        
        // Get title from user
        Alert.prompt(
          'Agenda Title',
          'Enter a title for this agenda:',
          [
            { text: 'Cancel', style: 'cancel' },
            {
              text: 'Upload',
              onPress: async (title) => {
                if (title) {
                  await uploadAgendaFile(asset, title);
                }
              },
            },
          ],
          'plain-text',
          'PM Connect 3.0 Event Agenda'
        );
      }
    } catch (error) {
      console.error('Error selecting PDF:', error);
      Alert.alert('Error', 'Failed to select PDF file');
    }
  };

  const uploadAgendaFile = async (asset: any, title: string) => {
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('title', title);
      formData.append('file', {
        uri: asset.uri,
        name: asset.name,
        type: 'application/pdf',
      } as any);

      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/agenda`, {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.ok) {
        const data = await response.json();
        Alert.alert('Success', 'Agenda uploaded successfully!');
        fetchCurrentAgenda(); // Refresh
      } else {
        const errorData = await response.json();
        Alert.alert('Upload Failed', errorData.detail || 'Failed to upload agenda');
      }
    } catch (error) {
      console.error('Error uploading agenda:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteAgenda = () => {
    Alert.alert(
      'Delete Agenda',
      'Are you sure you want to delete the current agenda? This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            // In a real app, we would call a delete API
            Alert.alert('Note', 'Delete functionality would be implemented here');
          },
        },
      ]
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
          <Text style={styles.headerTitle}>Agenda Management</Text>
        </View>

        {/* Upload Section */}
        <View style={styles.uploadSection}>
          <Text style={styles.sectionTitle}>📄 Upload New Agenda</Text>
          <Text style={styles.uploadDescription}>
            Upload a PDF file containing the event agenda. This will replace any existing agenda.
          </Text>
          <TouchableOpacity
            style={[styles.uploadButton, uploading && styles.uploadButtonDisabled]}
            onPress={handleUploadAgenda}
            disabled={uploading}
          >
            <Text style={styles.uploadButtonText}>
              {uploading ? '📄 Uploading...' : '📄 Select PDF File'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Current Agenda Section */}
        <View style={styles.currentAgendaSection}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>📋 Current Agenda</Text>
            {agenda && (
              <TouchableOpacity style={styles.refreshButton} onPress={fetchCurrentAgenda}>
                <Text style={styles.refreshButtonText}>🔄 Refresh</Text>
              </TouchableOpacity>
            )}
          </View>

          {loading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#007bff" />
              <Text style={styles.loadingText}>Loading agenda...</Text>
            </View>
          ) : agenda ? (
            <View style={styles.agendaCard}>
              <View style={styles.agendaHeader}>
                <Text style={styles.agendaTitle}>{agenda.agendaTitle}</Text>
                <TouchableOpacity
                  style={styles.deleteButton}
                  onPress={handleDeleteAgenda}
                >
                  <Text style={styles.deleteButtonText}>🗑️</Text>
                </TouchableOpacity>
              </View>
              
              <Text style={styles.agendaDate}>
                Uploaded: {new Date(agenda.uploadTimestamp).toLocaleDateString()} at{' '}
                {new Date(agenda.uploadTimestamp).toLocaleTimeString()}
              </Text>
              
              <View style={styles.agendaActions}>
                <TouchableOpacity style={styles.previewButton}>
                  <Text style={styles.previewButtonText}>👁️ Preview PDF</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.downloadButton}>
                  <Text style={styles.downloadButtonText}>⬇️ Download</Text>
                </TouchableOpacity>
              </View>
              
              <Text style={styles.agendaNote}>
                📝 This agenda is now visible to all event attendees in their event information page.
              </Text>
            </View>
          ) : (
            <View style={styles.noAgendaContainer}>
              <Text style={styles.noAgendaText}>📄 No agenda uploaded yet</Text>
              <Text style={styles.noAgendaSubtext}>
                Upload a PDF file to make the event agenda available to attendees
              </Text>
            </View>
          )}
        </View>

        {/* Instructions Section */}
        <View style={styles.instructionsSection}>
          <Text style={styles.sectionTitle}>💡 Instructions</Text>
          <View style={styles.instructionsList}>
            <View style={styles.instructionItem}>
              <Text style={styles.instructionNumber}>1</Text>
              <Text style={styles.instructionText}>
                Prepare your event agenda as a PDF file with clear formatting
              </Text>
            </View>
            <View style={styles.instructionItem}>
              <Text style={styles.instructionNumber}>2</Text>
              <Text style={styles.instructionText}>
                Click "Select PDF File" to choose your agenda document
              </Text>
            </View>
            <View style={styles.instructionItem}>
              <Text style={styles.instructionNumber}>3</Text>
              <Text style={styles.instructionText}>
                Enter a descriptive title for the agenda
              </Text>
            </View>
            <View style={styles.instructionItem}>
              <Text style={styles.instructionNumber}>4</Text>
              <Text style={styles.instructionText}>
                The agenda will be immediately available to all attendees
              </Text>
            </View>
          </View>
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>© 2025 Jakson Limited. Powered by AI.</Text>
        </View>
      </ScrollView>
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
  uploadSection: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 12,
  },
  uploadDescription: {
    fontSize: 14,
    color: '#6c757d',
    lineHeight: 20,
    marginBottom: 16,
  },
  uploadButton: {
    backgroundColor: '#28a745',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  uploadButtonDisabled: {
    opacity: 0.6,
  },
  uploadButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  currentAgendaSection: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
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
  agendaCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 20,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  agendaHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  agendaTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
    flex: 1,
    marginRight: 12,
  },
  deleteButton: {
    padding: 8,
  },
  deleteButtonText: {
    fontSize: 18,
  },
  agendaDate: {
    fontSize: 14,
    color: '#6c757d',
    marginBottom: 16,
  },
  agendaActions: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  previewButton: {
    flex: 1,
    backgroundColor: '#007bff',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  previewButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  downloadButton: {
    flex: 1,
    backgroundColor: '#6c757d',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  downloadButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  agendaNote: {
    fontSize: 12,
    color: '#28a745',
    fontStyle: 'italic',
    textAlign: 'center',
  },
  noAgendaContainer: {
    alignItems: 'center',
    padding: 32,
  },
  noAgendaText: {
    fontSize: 18,
    color: '#6c757d',
    marginBottom: 8,
  },
  noAgendaSubtext: {
    fontSize: 14,
    color: '#adb5bd',
    textAlign: 'center',
    lineHeight: 20,
  },
  instructionsSection: {
    padding: 24,
    backgroundColor: 'white',
    marginBottom: 16,
  },
  instructionsList: {
    gap: 16,
  },
  instructionItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  instructionNumber: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#007bff',
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
    textAlign: 'center',
    lineHeight: 24,
    marginRight: 12,
  },
  instructionText: {
    flex: 1,
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
});