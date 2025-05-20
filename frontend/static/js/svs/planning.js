const { createApp, ref, computed, onMounted, watch } = Vue;

// Create Axios instance with base URL and default settings
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

createApp({
  setup() {
    // Constants
    const RESERVATION_STATE_ACTIVE = 750; // Constant for reservation state

    const currentStep = ref(1);
    const reservationComplete = ref(false);

    // Available days data with loading and error states
    const availableDays = ref([]);
    const availableDaysLoading = ref(false);
    const availableDaysError = ref(null);
    const noAvailableDays = ref(false); // Flag to indicate no days are available

    const selectedDay = ref(null);
    const selectedTime = ref('');
    const username = ref('');
    const userId = ref('');
    const selectedAllianceId = ref('');
    const saveUserInfo = ref(true); // Default to true
    const isLoading = ref(false);
    const showConfirmationModal = ref(false);
    const currentReservationId = ref(null); // Store the current reservation ID

    // Error modal states
    const showErrorModal = ref(false);
    const errorMessage = ref("");
    const userIdError = ref(false);
    const userIdTooShort = ref(false);

    // Alliance data with IDs and names
    const alliances = ref([]);
    const alliancesLoading = ref(false);
    const alliancesError = ref(null);

    // All system reservations
    const allReservations = ref([]);

    // Reactive blockedSlots that will be populated from allReservations
    const blockedSlots = ref([]);

    // User lookup
    const userLookupLoading = ref(false);
    const userLookupError = ref(null);

    const availableTimes = ref([
      '00:00', '00:30', '01:00', '01:30', '02:00', '02:30',
      '03:00', '03:30', '04:00', '04:30', '05:00', '05:30',
      '06:00', '06:30', '07:00', '07:30', '08:00', '08:30',
      '09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
      '12:00', '12:30', '13:00', '13:30', '14:00', '14:30',
      '15:00', '15:30', '16:00', '16:30', '17:00', '17:30',
      '18:00', '18:30', '19:00', '19:30', '20:00', '20:30',
      '21:00', '21:30', '22:00', '22:30', '23:00', '23:30',
    ]);

    // Language selection and translations
    const savedLanguage = localStorage.getItem('svsLanguage') || 'en';
    const selectedLanguage = ref(savedLanguage);

    // Combine all translations
    const translations = {
      en: enTranslations,
      ar: arTranslations,
      zh: zhTranslations,
      ko: koTranslations,
      ja: jaTranslations,
      hi: hiTranslations,
      es: esTranslations,
      de: deTranslations,
      it: itTranslations,
      pt: ptTranslations,
      tr: trTranslations,
      fr: frTranslations,
    };

    // In the setup() function, add these reactive refs
    const showExportNotification = ref(false);
    const fadeExportNotification = ref(false);

    // Show notification function for calendar export
    function showNotification() {
      showExportNotification.value = true;
      fadeExportNotification.value = false;

      // Start fading after 2 seconds
      setTimeout(() => {
        fadeExportNotification.value = true;
      }, 2000);

      // Hide completely after 2.3 seconds (allowing for transition)
      setTimeout(() => {
        showExportNotification.value = false;
      }, 2300);
    }

    // Function to generate ICS content for calendar export
    function generateICSContent(data) {
      // Create a unique identifier for the event
      const uid = `${data.reservationId}@svs-minister-planning`;

      // Format the date and time for ICS (YYYYMMDDTHHMMSSZ format)
      const dateObj = new Date(data.date);
      const year = dateObj.getUTCFullYear();
      const month = String(dateObj.getUTCMonth() + 1).padStart(2, '0');
      const day = String(dateObj.getUTCDate()).padStart(2, '0');

      // Parse time (assuming format like "18:00")
      const [hours, minutes] = data.time.split(':');

      // Create start and end time (30 minute appointments)
      const startTime = `${year}${month}${day}T${hours}${minutes}00Z`;

      // Calculate end time (30 minutes later)
      let endHour = parseInt(hours);
      let endMinutes = parseInt(minutes) + 30;

      // Handle minute overflow
      if (endMinutes >= 60) {
        endHour += 1;
        endMinutes -= 60;
      }

      // Format with leading zeros
      const formattedEndHour = String(endHour).padStart(2, '0');
      const formattedEndMinutes = String(endMinutes).padStart(2, '0');

      const endTime = `${year}${month}${day}T${formattedEndHour}${formattedEndMinutes}00Z`;

      // Build the ICS content
      const icsContent = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//SVS Minister Planning//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        'BEGIN:VEVENT',
        `UID:${uid}`,
        `DTSTAMP:${startTime}`,
        `DTSTART:${startTime}`,
        `DTEND:${endTime}`,
        `SUMMARY:SVS Minister Meeting: ${data.type} - ${data.minister}`,
        `DESCRIPTION:Minister appointment with ${data.type} - ${data.minister}.\\nUser ID: ${data.userId}\\nUsername: ${data.username}\\nAlliance: ${data.alliance}\\nState: ${RESERVATION_STATE_ACTIVE}`,
        'END:VEVENT',
        'END:VCALENDAR'
      ].join('\r\n');

      return icsContent;
    }

    // Function to download ICS file
    function downloadICSFile(data) {
      const icsContent = generateICSContent(data);
      const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
      const url = URL.createObjectURL(blob);

      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `svs-minister-appointment-${data.date}.ics`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }

    // Function to export reservation to calendar
    function exportToCalendar() {
      const appointmentData = {
        reservationId: currentReservationId.value || `svs-${Date.now()}`, // Use stored ID or fallback
        userId: userId.value,
        username: username.value,
        alliance: getAllianceName(selectedAllianceId.value),
        date: selectedDay.value.date,
        type: selectedDay.value.type,
        minister: selectedDay.value.minister,
        time: selectedTime.value,
        state: RESERVATION_STATE_ACTIVE,
      };

      downloadICSFile(appointmentData);
      showNotification();
    }

    // Function to get language from URL query parameter
    function getLanguageFromUrl() {
      const urlParams = new URLSearchParams(window.location.search);
      const langParam = urlParams.get('lang');

      // Valid languages array - must match available options in dropdown
      const validLanguages = ['en', 'fr', 'ar', 'zh', 'ko', 'ja', 'hi', 'es', 'de', 'it', 'pt', 'tr'];

      // Check if the language parameter exists and is valid
      if (langParam && validLanguages.includes(langParam)) {
        return langParam;
      }

      // Return null if no valid language parameter is found
      return null;
    }

    // Function to update URL with language parameter
    function updateUrlWithLanguage(lang) {
      // Don't update URL if running without history API support
      if (!window.history || !window.history.replaceState) return;

      // Create URL object from current URL
      const url = new URL(window.location);

      // Set or update the lang parameter
      url.searchParams.set('lang', lang);

      // Update the URL without refreshing the page
      window.history.replaceState({}, '', url);
    }

    // Function to get translated text
    function translate(key) {
      if (translations[selectedLanguage.value] && translations[selectedLanguage.value][key]) {
        return translations[selectedLanguage.value][key];
      }
      // Fallback to English if translation not found
      return translations.en[key] || key;
    }

    // Function to change language - MODIFIED TO SUPPORT URL PARAMETER
    function changeLanguage(event) {
      const lang = event.target ? event.target.value : event;
      selectedLanguage.value = lang;
      document.documentElement.lang = lang;

      // Save language preference to localStorage
      try {
        localStorage.setItem('svsLanguage', lang);
      } catch (error) {
        console.error('Error saving language preference:', error);
      }

      // Handle right-to-left languages (Arabic)
      if (lang === 'ar') {
        document.documentElement.dir = 'rtl';
      } else {
        document.documentElement.dir = 'ltr';
      }

      // Update URL with the current language (without refreshing the page)
      updateUrlWithLanguage(lang);
    }

    // Function to fetch available days from API
    function fetchAvailableDays() {
      availableDaysLoading.value = true;
      availableDaysError.value = null;
      noAvailableDays.value = false;

      // Reset selection when fetching new days
      selectedDay.value = null;

      return new Promise((resolve, reject) => {
        api.get('/svs')
          .then(response => {
            availableDays.value = response.data;
            availableDaysLoading.value = false;

            // Set flag if no days are available
            if (response.data.length === 0) {
              noAvailableDays.value = true;
            }

            resolve(response.data);
          })
          .catch(error => {
            console.error('Error fetching available days:', error);
            availableDaysError.value = error.response ?
              error.response.data.message :
              'Failed to fetch available days';
            availableDaysLoading.value = false;

            // Fallback to default data in case of error
            // For production, we'll set an empty array to block progression
            availableDays.value = [];
            noAvailableDays.value = true;

            reject(error);
          });
      });
    }

    // Helper function to get alliance name from ID
    function getAllianceName(allianceId) {
      const alliance = alliances.value.find(a => a.id === allianceId);
      return alliance ? alliance.tag : 'Unknown Alliance';
    }

    // Function to get alliance ID from tag
    function getAllianceIdFromTag(tag) {
      if (!tag) return null;

      // Case insensitive search for the alliance tag
      const alliance = alliances.value.find(a =>
        a.tag.toLowerCase() === tag.toLowerCase()
      );

      return alliance ? alliance.id : null;
    }

    // Parse username in the format [AML]MMisha
    function parseAllianceUsername(input) {
      // Regex to match pattern [TagName]Username
      const regex = /^\[(.*?)\](.*)/;
      const match = input.match(regex);

      if (match && match.length >= 3) {
        return {
          allianceTag: match[1].trim(),
          username: match[2].trim()
        };
      }

      return null;
    }

    // Save user information to localStorage only if saveUserInfo is checked
    function saveToLocalStorage() {
      // Only save if we have valid data and saveUserInfo is checked
      if (saveUserInfo.value && userId.value && !userIdError.value) {
        try {
          const userInfo = {
            userId: userId.value,
            username: username.value || '',
            allianceId: selectedAllianceId.value || ''
          };

          localStorage.setItem('svsUserInfo', JSON.stringify(userInfo));
          console.log('User info saved to localStorage:', userInfo);
        } catch (error) {
          console.error('Error saving to localStorage:', error);
        }
      }
    }

    // Clear user information from localStorage
    function clearLocalStorage() {
      try {
        localStorage.removeItem('svsUserInfo');
        console.log('User info cleared from localStorage');
      } catch (error) {
        console.error('Error clearing localStorage:', error);
      }
    }

    // Watch for changes to saveUserInfo checkbox
    watch(saveUserInfo, (newValue) => {
      if (newValue) {
        // If checked and we have a valid user ID, save the current information
        if (userId.value && !userIdError.value) {
          saveToLocalStorage();
        }
      } else {
        // If unchecked, clear the stored information
        clearLocalStorage();
      }
    });

    // Validate UserID to contain only numbers and be at least 8 digits
    function validateUserId(input) {
      // Check if input is empty
      if (!input || input.trim() === '') {
        userIdError.value = false;
        userIdTooShort.value = false;
        return true;
      }

      // Check if input contains only digits
      const isNumeric = /^\d+$/.test(input);
      userIdError.value = !isNumeric;

      // Check if ID is at least 8 digits long
      if (isNumeric) {
        userIdTooShort.value = input.length < 8;
        return !userIdTooShort.value;
      }

      return false;
    }

    // Handle userId input to enforce numeric values
    function handleUserIdInput() {
      // Remove any non-numeric characters
      if (userId.value) {
        const numericValue = userId.value.replace(/\D/g, '');

        // Only update if the value would change to avoid cursor issues
        if (numericValue !== userId.value) {
          userId.value = numericValue;
        }

        validateUserId(userId.value);

        // Save to localStorage after a delay if saveUserInfo is checked
        if (saveUserInfo.value) {
          setTimeout(() => {
            if (userId.value === numericValue) { // Only save if value hasn't changed
              saveToLocalStorage();
            }
          }, 1000);
        }
      }
    }

    // Function to handle username input and check for alliance tag format
    function handleUsernameInput() {
      const input = username.value;

      // Check if input contains [tag] format
      if (input && input.includes('[') && input.includes(']')) {
        const parsed = parseAllianceUsername(input);

        if (parsed) {
          // Find alliance by tag
          const allianceId = getAllianceIdFromTag(parsed.allianceTag);

          if (allianceId) {
            // Set alliance dropdown
            selectedAllianceId.value = allianceId;

            // Remove alliance tag from username
            username.value = parsed.username;

            console.log(`Detected alliance tag [${parsed.allianceTag}] and set username to ${parsed.username}`);

            // Save the updated information to localStorage if saveUserInfo is checked
            if (saveUserInfo.value) {
              saveToLocalStorage();
            }
          }
        }
      } else if (saveUserInfo.value) {
        // Save to localStorage even without alliance tag detection if saveUserInfo is checked
        saveToLocalStorage();
      }
    }

    const hasBlockedDates = computed(() => {
      return availableDays.value.some(day => isDateBlocked(day));
    });

    const hasBlockedTimes = computed(() => {
      return availableTimes.value.some(time => isTimeBlocked(time));
    });

    // Computed property to check if no days are available or there was an error loading days
    const hasNoAvailableDays = computed(() => {
      return (noAvailableDays.value || (availableDays.value.length === 0 && !availableDaysLoading.value && !availableDaysError.value));
    });

    // Computed property to determine if user can proceed to date selection
    const canProceedToDateSelection = computed(() => {
      // If we're still loading days, we can't determine if we can proceed yet
      if (availableDaysLoading.value) {
        return false;
      }

      // If there was an error loading days or no days are available, don't proceed
      if (availableDaysError.value || noAvailableDays.value || availableDays.value.length === 0) {
        return false;
      }

      // If all checks pass, user can proceed
      return true;
    });

    // Watch for changes in username and alliance and save to localStorage if saveUserInfo is checked
    watch([username, selectedAllianceId], () => {
      // Don't immediately save when these change due to API lookup
      // We have a debounced version that will save after typing stops
      if (!userLookupLoading.value && saveUserInfo.value) {
        saveToLocalStorage();
      }
    });

    // Look up user information based on ID using Axios API
    function lookupUserInfo() {
      // Only lookup if userId is valid (numeric and at least 8 digits)
      if (userId.value && userId.value.trim() !== '' && !userIdError.value && !userIdTooShort.value) {
        userLookupLoading.value = true;
        userLookupError.value = null;

        // Using Axios instance to get user information
        api.get(`/users/${userId.value}`)
          .then(response => {
            // Update user information from API response
            const userData = response.data;
            username.value = userData.username || '';
            selectedAllianceId.value = userData.alliance.id || '';
            userLookupLoading.value = false;

            // Save to localStorage if saveUserInfo is checked
            if (saveUserInfo.value) {
              saveToLocalStorage();
            }
          })
          .catch(error => {
            console.error('Error looking up user:', error);

            userLookupError.value = error.response ? error.response.data.message : 'User not found';
            userLookupLoading.value = false;

            // Try localStorage as fallback only if saveUserInfo is checked
            if (saveUserInfo.value) {
              try {
                const storedUserInfo = localStorage.getItem('svsUserInfo');
                if (storedUserInfo) {
                  const userInfo = JSON.parse(storedUserInfo);
                  // Only use localStorage values if the IDs match
                  if (userInfo.userId === userId.value) {
                    username.value = userInfo.username || '';
                    selectedAllianceId.value = userInfo.allianceId || '';
                  } else {
                    // Clear fields if ID doesn't match stored ID
                    username.value = '';
                    selectedAllianceId.value = '';
                  }
                } else {
                  // Clear fields if no stored data
                  username.value = '';
                  selectedAllianceId.value = '';
                }
              } catch (storageError) {
                console.error('Error loading user info from localStorage:', storageError);
                username.value = '';
                selectedAllianceId.value = '';
              }
            } else {
              // Clear fields if no localStorage should be used
              username.value = '';
              selectedAllianceId.value = '';
            }
          });
      } else {
        // Clear fields if no ID provided or ID has errors or too short
        username.value = '';
        selectedAllianceId.value = '';
        userLookupError.value = null;
      }
    }

    // Fetch all reservations (not just for the current user)
    function fetchAllReservations() {
      isLoading.value = true;

      return new Promise((resolve, reject) => {
        // Using Axios to fetch all reservations
        api.get('/reservations')
          .then(response => {
            isLoading.value = false;

            // Store all reservations
            allReservations.value = response.data;

            // Update blockedSlots based on all reservations
            updateBlockedSlots();

            resolve(response.data);
          })
          .catch(error => {
            console.error('Error fetching all reservations:', error);
            isLoading.value = false;

            // Return empty array on error
            allReservations.value = [];
            blockedSlots.value = [];
            resolve([]);
          });
      });
    }

    // Function to update blockedSlots based on allReservations
    function updateBlockedSlots() {
      // Clear existing blocked slots
      blockedSlots.value = [];

      console.debug(allReservations);

      // Create blocked slots from all reservations
      allReservations.value.forEach(reservation => {
        blockedSlots.value.push({
          date: reservation.schedule_date,
          time: reservation.schedule_time
        });
      });

      console.debug(blockedSlots);
    }

    // Check if a specific date is blocked for the current user
    function isDateBlocked(day) {
      // Check if the user has any reservations on this day
      return allReservations.value.some(reservation =>
        reservation.schedule_date === day.date &&
        reservation.user.id === parseInt(userId.value)
      );
    }

    // Check if a time is blocked (either generally or for user-specific reasons)
    function isTimeBlocked(time) {
      if (!selectedDay.value) return false;

      // Check general blocked slots
      const generalBlocked = blockedSlots.value.some(
        slot => slot.date === selectedDay.value.date && slot.time === time
      );

      // Check if this specific date+time is already reserved by anyone
      const alreadyReserved = allReservations.value.some(
        reservation =>
          reservation.schedule_date === selectedDay.value.date &&
          reservation.schedule_time === time &&
          // Also verify it's the same minister type and minister ID
          reservation.minister_type_id === getMinisterTypeId(selectedDay.value.type) &&
          reservation.minister_id === getMinisterPositionId(selectedDay.value.minister)
      );

      // Check user-specific blocked slots
      const userBlocked = isUserSpecificTimeBlocked(time);

      return generalBlocked || alreadyReserved || userBlocked;
    }

    // Check if a time is blocked specifically for this user
    function isUserSpecificTimeBlocked(time) {
      if (!selectedDay.value || !userId.value) return false;

      return allReservations.value.some(
        reservation =>
          reservation.schedule_date === selectedDay.value.date &&
          reservation.schedule_time === time &&
          reservation.user.id === parseInt(userId.value)
      );
    }

    function checkUserReservationsAndProceed() {
      if (username.value && userId.value && selectedAllianceId.value && !userIdError.value && !userIdTooShort.value) {
        isLoading.value = true;

        // Fetch all reservations and available days
        Promise.all([
          fetchAllReservations(),
          fetchAvailableDays()
        ]).then(([resData, daysData]) => {
          // Check if we have available days
          if (availableDays.value.length > 0 && !noAvailableDays.value) {
            isLoading.value = false;
            nextStep();
          } else {
            isLoading.value = false;

            // Only proceed if there are available days
            if (canProceedToDateSelection.value) {
              nextStep();
            } else {
              // Show an error modal if no days are available
              errorMessage.value = "No minister slots are currently available. Please try again later.";
              showErrorModal.value = true;
            }
          }
        }).catch(error => {
          isLoading.value = false;
          errorMessage.value = "Error loading data. Please try again.";
          showErrorModal.value = true;
        });
      }
    }

    // Function to fetch alliances from API using Axios
    function fetchAlliances() {
      alliancesLoading.value = true;
      alliancesError.value = null;

      api.get('/alliances')
        .then(response => {
          alliances.value = response.data;
          alliancesLoading.value = false;
        })
        .catch(error => {
          console.error('Error fetching alliances:', error);
          alliancesError.value = error.response ? error.response.data.message : 'Failed to fetch alliances';
          alliancesLoading.value = false;

          // Fallback to default alliances in case of error
          alliances.value = [
            { id: '1', tag: 'AML' },
            { id: '2', tag: 'SVS' },
            { id: '3', tag: 'TDM' },
            { id: '4', tag: 'BRV' },
            { id: '5', tag: 'GSR' }
          ];
        });
    }

    // MODIFIED onMounted to check for URL language parameter first
    onMounted(() => {
      // Check for language in URL first (highest priority)
      const urlLanguage = getLanguageFromUrl();
      if (urlLanguage) {
        // Update the selected language
        selectedLanguage.value = urlLanguage;
        // Apply the language change
        changeLanguage(urlLanguage);
      }

      // Fetch alliances
      fetchAlliances();

      // Fetch available days and all reservations in parallel
      Promise.all([
        fetchAvailableDays(),
        fetchAllReservations()
      ]).then(([days, reservations]) => {
        // Store all reservations and update blocked slots
        allReservations.value = reservations;
        updateBlockedSlots();
      }).catch(error => {
        console.error('Error fetching initial data:', error);
      });

      // Only load from localStorage if saveUserInfo is true by default
      if (saveUserInfo.value) {
        try {
          const storedUserInfo = localStorage.getItem('svsUserInfo');

          if (storedUserInfo) {
            const userInfo = JSON.parse(storedUserInfo);
            userId.value = userInfo.userId || '';
            username.value = userInfo.username || '';
            selectedAllianceId.value = userInfo.allianceId || '';

            // Validate the user ID
            validateUserId(userId.value);

            // After setting the userId, we'll trigger the auto-lookup
            // which will populate username and alliance if found - only if valid and long enough
            if (!userIdError.value && !userIdTooShort.value) {
              lookupUserInfo(); // This will override the localStorage values with API data if found
            }
          }
        } catch (error) {
          console.error('Error loading user info from localStorage:', error);
        }
      }
    });

    // Watch for changes in userId to update reservations
    watch(userId, () => {
      selectedDay.value = null;
      selectedTime.value = '';

      // Look up user info whenever ID changes if it's valid and long enough
      if (!userIdError.value && !userIdTooShort.value && userId.value && userId.value.trim() !== '') {
        lookupUserInfo();
      }
    });

    const canReserve = computed(() => {
      return selectedDay.value &&
             selectedTime.value &&
             username.value &&
             userId.value &&
             selectedAllianceId.value &&
             !userIdError.value &&
             !userIdTooShort.value;
    });

    function formatDate(dateString) {
      const date = new Date(dateString);
      const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
      const months = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December'];
      return `${days[date.getUTCDay()]}, ${months[date.getUTCMonth()]} ${date.getUTCDate()}`;
    }

    function selectDate(day) {
      if (!isDateBlocked(day)) {
        selectedDay.value = day;
        selectedTime.value = ''; // Reset time selection when date changes
      }
    }

    function selectTime(time) {
      if (!isTimeBlocked(time)) {
        selectedTime.value = time;
      }
    }

    function clearUserId() {
      userId.value = '';
      username.value = '';
      selectedAllianceId.value = '';
      userLookupError.value = null;
      userIdError.value = false;
      userIdTooShort.value = false;

      // Clear localStorage if saveUserInfo is checked
      if (saveUserInfo.value) {
        clearLocalStorage();
      }
    }

    function nextStep() {
      if (currentStep.value < 4) {
        // Special check for step 1 to 2 transition (going to date selection)
        if (currentStep.value === 1 && !canProceedToDateSelection.value) {
          errorMessage.value = "No minister slots are currently available. Please try again later.";
          showErrorModal.value = true;
          return;
        }

        currentStep.value++;
      }
    }

    function prevStep() {
      if (currentStep.value > 1) currentStep.value--;
    }

    function confirmReservation() {
      if (canReserve.value) {
        showConfirmationModal.value = true;
      }
    }

    // Close error modal function
    function closeErrorModal() {
      showErrorModal.value = false;
    }

    // Helper function to get minister ID based on type
    function getMinisterTypeId(ministerType) {
      const ministerTypes = {
        'Construction Day': 1,
        'Research Day': 2,
        'Training Day': 3
      };
      return ministerTypes[ministerType] || 1;
    }

    // Helper function to get minister position ID
    function getMinisterPositionId(ministerPosition) {
      const ministerPositions = {
        'Vice President': 1,
        'Minister of Education': 2
      };
      return ministerPositions[ministerPosition] || 1;
    }

    // Format date for API consumption (YYYY-MM-DD)
    function formatDateForAPI(dateString) {
      return dateString; // Already in correct format: '2025-04-21'
    }

    // Format time for API consumption (HH:MM) - no seconds
    function formatTimeForAPI(timeString) {
      return timeString; // Return without adding seconds: '14:30'
    }

    // Function to handle the "Try a Different Time" button click
    function tryDifferentTime() {
      // Close the error modal
      showErrorModal.value = false;

      // If we're currently in step 4 (confirmation), go back to step 3 (time selection)
      if (currentStep.value === 4) {
        currentStep.value = 3;
      }

      // Clear the selected time to allow for a new selection
      selectedTime.value = '';
    }

    async function finalizeReservation() {
      showConfirmationModal.value = false;

      // Save user info to localStorage if option is checked
      if (saveUserInfo.value) {
        saveToLocalStorage();
      }

      // Create the reservation payload with properly formatted date/time data
      const reservationData = {
        user: {
          id: parseInt(userId.value),
          username: username.value
        },
        alliance: {
          id: parseInt(selectedAllianceId.value),
          tag: getAllianceName(selectedAllianceId.value)
        },
        schedule: {
          date: formatDateForAPI(selectedDay.value.date),
          time: formatTimeForAPI(selectedTime.value)
        },
        minister: {
          id: getMinisterPositionId(selectedDay.value.minister),
          type: getMinisterTypeId(selectedDay.value.type),
          name: selectedDay.value.minister,
          typeName: selectedDay.value.type
        },
        state: {
          id: RESERVATION_STATE_ACTIVE
        }
      };

      try {
        console.log('Sending reservation request with data:', reservationData);

        // Make POST request to the reservations API using axios
        const response = await api.post('/reservations', reservationData);

        console.log('Reservation successful:', response.data);

        // Store the reservation ID from the API response
        currentReservationId.value = response.data.id;

        // Add to allReservations and update blockedSlots for UI purposes
        const newReservation = {
          user_id: parseInt(userId.value),
          schedule_date: selectedDay.value.date,
          schedule_time: selectedTime.value,
          minister_id: getMinisterPositionId(selectedDay.value.minister),
          minister_type_id: getMinisterTypeId(selectedDay.value.type),
          alliance_id: parseInt(selectedAllianceId.value),
          state_id: RESERVATION_STATE_ACTIVE,
          id: response.data.id
        };

        allReservations.value.push(newReservation);

        // Update blocked slots
        updateBlockedSlots();

        // Set reservation as complete (which shows success view)
        reservationComplete.value = true;
      } catch (error) {
        console.error('Error creating reservation:', error.response?.data || error.message);

        // Show error modal with appropriate message
        if (error.response && error.response.data && error.response.data.message) {
          errorMessage.value = error.response.data.message;
        } else if (error.response && error.response.status === 409) {
          errorMessage.value = "This time slot has already been reserved by another player.";
        } else if (error.response && error.response.status === 403) {
          errorMessage.value = "You have exceeded your reservation limit.";
        } else if (!navigator.onLine) {
          errorMessage.value = "No internet connection. Please check your network and try again.";
        } else {
          errorMessage.value = "Unable to complete your reservation. Please try again later.";
        }
        showErrorModal.value = true;
      }
    }

    function resetForm() {
      currentStep.value = 1;
      reservationComplete.value = false;
      selectedDay.value = null;
      selectedTime.value = '';
      showConfirmationModal.value = false;
      userIdError.value = false;
      userIdTooShort.value = false;
      currentReservationId.value = null; // Reset the reservation ID

      // If saveUserInfo is unchecked, clear the user fields
      if (!saveUserInfo.value) {
        userId.value = '';
        username.value = '';
        selectedAllianceId.value = '';
      }

      // Clear all reservations and fetch them again
      allReservations.value = [];
      blockedSlots.value = [];

      // Refresh available days and all reservations
      Promise.all([
        fetchAvailableDays(),
        fetchAllReservations()
      ]).catch(error => {
        console.error('Error fetching data on reset:', error);
      });
    }

    // Debounce the user lookup to avoid excessive API calls
    const debouncedLookupUserInfo = (function() {
      let timer;

      return function() {
        clearTimeout(timer);

        timer = setTimeout(() => {
          if (userId.value && userId.value.trim() !== '' && !userIdError.value && !userIdTooShort.value) {
            lookupUserInfo();
          }
        }, 500); // Wait 500ms after user stops typing
      };
    })();

    // Create a debounced version of handleUsernameInput to avoid excessive processing
    const debouncedHandleUsernameInput = (function() {
      let timer;

      return function() {
        clearTimeout(timer);

        timer = setTimeout(() => {
          if (username.value !== undefined) {
            handleUsernameInput();
          }
        }, 300); // 300ms debounce delay
      };
    })();

    // Create a debounced version of handleUserIdInput to avoid excessive processing
    const debouncedHandleUserIdInput = (function() {
      let timer;

      return function() {
        clearTimeout(timer);

        timer = setTimeout(() => {
          if (userId.value !== undefined) {
            handleUserIdInput();
          }
        }, 300); // 300ms debounce delay
      };
    })();

    return {
      currentStep,
      reservationComplete,
      availableDays,
      availableDaysLoading,
      availableDaysError,
      noAvailableDays,
      hasNoAvailableDays,
      selectedDay,
      selectedTime,
      username,
      userId,
      selectedAllianceId,
      saveUserInfo,
      availableTimes,
      isLoading,
      canReserve,
      canProceedToDateSelection,
      hasBlockedDates,
      hasBlockedTimes,
      alliances,
      alliancesLoading,
      alliancesError,
      userLookupLoading,
      userLookupError,
      userIdError,
      userIdTooShort,
      debouncedLookupUserInfo,
      debouncedHandleUsernameInput,
      debouncedHandleUserIdInput,
      showConfirmationModal,
      showErrorModal,
      errorMessage,
      formatDate,
      selectDate,
      selectTime,
      clearUserId,
      nextStep,
      prevStep,
      confirmReservation,
      finalizeReservation,
      resetForm,
      isTimeBlocked,
      isDateBlocked,
      isUserSpecificTimeBlocked,
      checkUserReservationsAndProceed,
      lookupUserInfo,
      getAllianceName,
      fetchAlliances,
      fetchAvailableDays,
      fetchAllReservations,
      closeErrorModal,
      handleUsernameInput,
      handleUserIdInput,
      validateUserId,
      saveToLocalStorage,
      clearLocalStorage,
      tryDifferentTime,
      selectedLanguage,
      translate,
      changeLanguage,
      showExportNotification,
      fadeExportNotification,
      exportToCalendar,
      showNotification,
      generateICSContent,
      downloadICSFile,
      allReservations,
      blockedSlots,
      updateBlockedSlots,
      currentReservationId,
      RESERVATION_STATE_ACTIVE,
      getLanguageFromUrl,
      updateUrlWithLanguage
    };
  }
}).mount('#app');