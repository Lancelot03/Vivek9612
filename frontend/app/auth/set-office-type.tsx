import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { useAuth } from '../../contexts/AuthContext';

export default function OfficeTypeScreen() {
  const params = useLocalSearchParams();
  const { employeeCode } = params;

  const [selectedOfficeType, setSelectedOfficeType] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const { setOfficeType } = useAuth();

  const officeTypes = [
    {
      type: 'Head Office',
      description: 'Corporate headquarters and main offices',
      icon: '🏢',
    },
    {
      type: 'Site Office',
      description: 'Project sites and field offices',
      icon: '🏗️',
    },
  ];

  const handleSetOfficeType = async () => {
    if (!selectedOfficeType) {
      Alert.alert('Error', 'Please select your office type');
      return;
    }

    setIsLoading(true);
    try {
      await setOfficeType(employeeCode as string, selectedOfficeType);

      Alert.alert(
        'Success',
        'Your profile has been set up successfully!',
        [
          {
            text: 'Continue',
            onPress: () => {
              // Navigate to appropriate dashboard based on role
              router.replace('/');
            },
          },
        ]
      );
    } catch (error: any) {
      console.error('Set office type error:', error);
      Alert.alert(
        'Error',
        error.message || 'Failed to set office type. Please try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerIcon}>🏢</Text>
          <Text style={styles.title}>Select Your Office Type</Text>
          <Text style={styles.subtitle}>
            Please select which type of office you work from. This helps us customize your experience.
          </Text>
        </View>

        {/* Office Type Selection */}
        <View style={styles.selectionContainer}>
          {officeTypes.map((office) => (
            <TouchableOpacity
              key={office.type}
              style={[
                styles.officeCard,
                selectedOfficeType === office.type && styles.selectedOfficeCard,
              ]}
              onPress={() => setSelectedOfficeType(office.type)}
              disabled={isLoading}
            >
              <View style={styles.officeCardContent}>
                <Text style={styles.officeIcon}>{office.icon}</Text>
                <View style={styles.officeInfo}>
                  <Text
                    style={[
                      styles.officeTitle,
                      selectedOfficeType === office.type && styles.selectedOfficeTitle,
                    ]}
                  >
                    {office.type}
                  </Text>
                  <Text
                    style={[
                      styles.officeDescription,
                      selectedOfficeType === office.type && styles.selectedOfficeDescription,
                    ]}
                  >
                    {office.description}
                  </Text>
                </View>
                <View style={styles.radioContainer}>
                  <View
                    style={[
                      styles.radioCircle,
                      selectedOfficeType === office.type && styles.selectedRadioCircle,
                    ]}
                  >
                    {selectedOfficeType === office.type && (
                      <View style={styles.radioInner} />
                    )}
                  </View>
                </View>
              </View>
            </TouchableOpacity>
          ))}
        </View>

        {/* Continue Button */}
        <TouchableOpacity
          style={[
            styles.continueButton,
            (!selectedOfficeType || isLoading) && styles.continueButtonDisabled,
          ]}
          onPress={handleSetOfficeType}
          disabled={!selectedOfficeType || isLoading}
        >
          {isLoading ? (
            <ActivityIndicator color="white" size="small" />
          ) : (
            <Text style={styles.continueButtonText}>Continue</Text>
          )}
        </TouchableOpacity>

        {/* Info Section */}
        <View style={styles.infoContainer}>
          <Text style={styles.infoTitle}>Why do we ask this?</Text>
          <Text style={styles.infoText}>
            • Customize your dashboard based on your work environment{'\n'}
            • Provide relevant event logistics and information{'\n'}
            • Help us understand our attendee demographics{'\n'}
            • You can change this later in your profile settings
          </Text>
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>© 2025 Jakson Limited. Powered by AI.</Text>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  content: {
    flex: 1,
    padding: 24,
    justifyContent: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  headerIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#2c3e50',
    textAlign: 'center',
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    color: '#6c757d',
    textAlign: 'center',
    lineHeight: 22,
  },
  selectionContainer: {
    marginBottom: 32,
  },
  officeCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 2,
    borderColor: '#e9ecef',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  selectedOfficeCard: {
    borderColor: '#007bff',
    backgroundColor: '#f8fcff',
  },
  officeCardContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  officeIcon: {
    fontSize: 40,
    marginRight: 16,
  },
  officeInfo: {
    flex: 1,
  },
  officeTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 4,
  },
  selectedOfficeTitle: {
    color: '#007bff',
  },
  officeDescription: {
    fontSize: 14,
    color: '#6c757d',
    lineHeight: 20,
  },
  selectedOfficeDescription: {
    color: '#0056b3',
  },
  radioContainer: {
    marginLeft: 16,
  },
  radioCircle: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#ced4da',
    alignItems: 'center',
    justifyContent: 'center',
  },
  selectedRadioCircle: {
    borderColor: '#007bff',
  },
  radioInner: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#007bff',
  },
  continueButton: {
    backgroundColor: '#007bff',
    padding: 18,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 24,
  },
  continueButtonDisabled: {
    backgroundColor: '#6c757d',
    opacity: 0.6,
  },
  continueButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  infoContainer: {
    backgroundColor: '#e7f3ff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    borderLeftWidth: 4,
    borderLeftColor: '#007bff',
  },
  infoTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 12,
    color: '#6c757d',
    lineHeight: 18,
  },
  footer: {
    alignItems: 'center',
    marginTop: 'auto',
  },
  footerText: {
    fontSize: 14,
    color: '#adb5bd',
  },
});