import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import * as Constants from 'expo-constants';

const EXPO_PUBLIC_BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || process.env.EXPO_PUBLIC_BACKEND_URL;

export default function RSVPForm() {
  const params = useLocalSearchParams();
  const { employeeId, employeeName, cadre, projectName } = params;

  const [mobileNumber, setMobileNumber] = useState('');
  const [requiresAccommodation, setRequiresAccommodation] = useState<boolean | null>(null);
  const [arrivalDate, setArrivalDate] = useState('');
  const [departureDate, setDepartureDate] = useState('');
  const [foodPreference, setFoodPreference] = useState('');
  // Sprint 3: Flight Time Preferences
  const [departureTimePreference, setDepartureTimePreference] = useState('');
  const [arrivalTimePreference, setArrivalTimePreference] = useState('');
  const [specialFlightRequirements, setSpecialFlightRequirements] = useState('');
  const [loading, setLoading] = useState(false);

  const validateForm = () => {
    if (!mobileNumber.trim()) {
      Alert.alert('Error', 'Please enter your mobile number');
      return false;
    }

    if (mobileNumber.length < 10) {
      Alert.alert('Error', 'Please enter a valid mobile number');
      return false;
    }

    if (requiresAccommodation === null) {
      Alert.alert('Error', 'Please select accommodation preference');
      return false;
    }

    if (requiresAccommodation && (!arrivalDate || !departureDate)) {
      Alert.alert('Error', 'Please select arrival and departure dates for accommodation');
      return false;
    }

    if (!foodPreference) {
      Alert.alert('Error', 'Please select your food preference');
      return false;
    }

    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setLoading(true);
    try {
      const responseData = {
        employeeId: employeeId as string,
        mobileNumber: mobileNumber.trim(),
        requiresAccommodation: requiresAccommodation!,
        arrivalDate: requiresAccommodation ? arrivalDate : null,
        departureDate: requiresAccommodation ? departureDate : null,
        foodPreference,
      };

      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/responses`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(responseData),
      });

      if (response.ok) {
        Alert.alert(
          'Success!',
          'Your response has been recorded successfully!',
          [
            {
              text: 'Continue',
              onPress: () => {
                router.replace({
                  pathname: '/event-info',
                  params: { employeeId: employeeId as string },
                });
              },
            },
          ]
        );
      } else {
        const errorData = await response.json();
        Alert.alert('Error', errorData.detail || 'Failed to submit response');
      }
    } catch (error) {
      console.error('Error submitting response:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        style={styles.keyboardAvoidingView}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
              <Text style={styles.backButtonText}>← Back</Text>
            </TouchableOpacity>
            <Text style={styles.headerTitle}>RSVP Form</Text>
          </View>

          {/* Employee Info */}
          <View style={styles.employeeSection}>
            <Text style={styles.sectionTitle}>Employee Information</Text>
            <View style={styles.infoCard}>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Name:</Text>
                <Text style={styles.infoValue}>{employeeName}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Employee ID:</Text>
                <Text style={styles.infoValue}>{employeeId}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Cadre:</Text>
                <Text style={styles.infoValue}>{cadre}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Project:</Text>
                <Text style={styles.infoValue}>{projectName}</Text>
              </View>
            </View>
          </View>

          {/* RSVP Form */}
          <View style={styles.formSection}>
            <Text style={styles.sectionTitle}>RSVP Details</Text>

            {/* Mobile Number */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Mobile Number *</Text>
              <TextInput
                style={styles.textInput}
                value={mobileNumber}
                onChangeText={setMobileNumber}
                placeholder="Enter your mobile number"
                keyboardType="phone-pad"
                maxLength={10}
              />
            </View>

            {/* Accommodation */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Do you require accommodation? *</Text>
              <View style={styles.radioGroup}>
                <TouchableOpacity
                  style={[
                    styles.radioOption,
                    requiresAccommodation === true && styles.radioOptionSelected,
                  ]}
                  onPress={() => setRequiresAccommodation(true)}
                >
                  <View
                    style={[
                      styles.radioCircle,
                      requiresAccommodation === true && styles.radioCircleSelected,
                    ]}
                  />
                  <Text
                    style={[
                      styles.radioText,
                      requiresAccommodation === true && styles.radioTextSelected,
                    ]}
                  >
                    Yes
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[
                    styles.radioOption,
                    requiresAccommodation === false && styles.radioOptionSelected,
                  ]}
                  onPress={() => setRequiresAccommodation(false)}
                >
                  <View
                    style={[
                      styles.radioCircle,
                      requiresAccommodation === false && styles.radioCircleSelected,
                    ]}
                  />
                  <Text
                    style={[
                      styles.radioText,
                      requiresAccommodation === false && styles.radioTextSelected,
                    ]}
                  >
                    No
                  </Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* Conditional Date Fields */}
            {requiresAccommodation && (
              <>
                <View style={styles.inputGroup}>
                  <Text style={styles.inputLabel}>Date of Arrival *</Text>
                  <TextInput
                    style={styles.textInput}
                    value={arrivalDate}
                    onChangeText={setArrivalDate}
                    placeholder="YYYY-MM-DD"
                  />
                </View>
                <View style={styles.inputGroup}>
                  <Text style={styles.inputLabel}>Expected Date of Departure *</Text>
                  <TextInput
                    style={styles.textInput}
                    value={departureDate}
                    onChangeText={setDepartureDate}
                    placeholder="YYYY-MM-DD"
                  />
                </View>
              </>
            )}

            {/* Food Preference */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Food Preference *</Text>
              <View style={styles.foodPreferenceGroup}>
                {['Veg', 'Non-Veg', 'Not Required'].map((option) => (
                  <TouchableOpacity
                    key={option}
                    style={[
                      styles.foodOption,
                      foodPreference === option && styles.foodOptionSelected,
                    ]}
                    onPress={() => setFoodPreference(option)}
                  >
                    <Text
                      style={[
                        styles.foodOptionText,
                        foodPreference === option && styles.foodOptionTextSelected,
                      ]}
                    >
                      {option}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            {/* Submit Button */}
            <TouchableOpacity
              style={[styles.submitButton, loading && styles.submitButtonDisabled]}
              onPress={handleSubmit}
              disabled={loading}
            >
              <Text style={styles.submitButtonText}>
                {loading ? 'Submitting...' : 'Submit Details'}
              </Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  keyboardAvoidingView: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 32,
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
  employeeSection: {
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
  infoCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  infoRow: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  infoLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6c757d',
    width: 100,
  },
  infoValue: {
    fontSize: 14,
    color: '#2c3e50',
    flex: 1,
  },
  formSection: {
    padding: 24,
    backgroundColor: 'white',
  },
  inputGroup: {
    marginBottom: 24,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#2c3e50',
    marginBottom: 8,
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#ced4da',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: 'white',
  },
  radioGroup: {
    flexDirection: 'row',
    gap: 16,
  },
  radioOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ced4da',
    backgroundColor: 'white',
    flex: 1,
  },
  radioOptionSelected: {
    borderColor: '#007bff',
    backgroundColor: '#e7f3ff',
  },
  radioCircle: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#ced4da',
    marginRight: 8,
  },
  radioCircleSelected: {
    borderColor: '#007bff',
    backgroundColor: '#007bff',
  },
  radioText: {
    fontSize: 16,
    color: '#6c757d',
  },
  radioTextSelected: {
    color: '#007bff',
    fontWeight: '600',
  },
  foodPreferenceGroup: {
    gap: 12,
  },
  foodOption: {
    padding: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ced4da',
    backgroundColor: 'white',
    alignItems: 'center',
  },
  foodOptionSelected: {
    borderColor: '#007bff',
    backgroundColor: '#e7f3ff',
  },
  foodOptionText: {
    fontSize: 16,
    color: '#6c757d',
    fontWeight: '500',
  },
  foodOptionTextSelected: {
    color: '#007bff',
    fontWeight: '600',
  },
  submitButton: {
    backgroundColor: '#007bff',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 16,
  },
  submitButtonDisabled: {
    opacity: 0.6,
  },
  submitButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
});