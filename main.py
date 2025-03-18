import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import axios from 'axios';
import * as Location from 'expo-location';
import * as ImagePicker from 'expo-image-picker';
import { Text, View, Button, Image, ScrollView, TextInput, Picker, Alert } from 'react-native';
import { useNavigation } from '@react-navigation/native';

// Navigation Setup
const Stack = createStackNavigator();

function SignIn() {
  const navigation = useNavigation();
  const [operators, setOperators] = useState([]);
  const [selectedOperator, setSelectedOperator] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    axios.get('https://fastapi-cloud-app-3.onrender.com/operators/')
      .then(response => setOperators(response.data))
      .catch(error => setError('Failed to load operators'));
  }, []);

  const handleLogin = () => {
    axios.post('https://fastapi-cloud-app-3.onrender.com/login/', {
      username: selectedOperator,
      password: password
    })
    .then(response => {
      localStorage.setItem('operator', selectedOperator);
      navigation.navigate('Home');
    })
    .catch(error => setError('Login failed: ' + error.response.data.detail));
  };

  return (
    <ScrollView contentContainerStyle={{ flexGrow: 1, justifyContent: 'center', alignItems: 'center', padding: 20 }}>
      <Image source={{ uri: 'https://via.placeholder.com/200x50?text=TICKCONTROL+LLC' }} style={{ width: 200, height: 50, marginBottom: 20 }} />
      <Text style={{ fontSize: 20, marginBottom: 10 }}>WELCOME TO TICK CONTROL, LLC</Text>
      <Text style={{ fontSize: 18, marginBottom: 10 }}>PLEASE LOG IN</Text>
      {error ? <Text style={{ color: 'red', marginBottom: 10 }}>{error}</Text> : null}
      <Picker
        selectedValue={selectedOperator}
        onValueChange={(itemValue) => setSelectedOperator(itemValue)}
        style={{ height: 50, width: 200, marginBottom: 10 }}
      >
        <Picker.Item label="Select Your Name" value="" />
        {operators.map(op => <Picker.Item key={op.id} label={op.name} value={op.name} />)}
      </Picker>
      <TextInput
        style={{ height: 40, width: 200, borderColor: 'gray', borderWidth: 1, marginBottom: 10, padding: 10 }}
        placeholder="PASSWORD"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />
      <Button title="SUBMIT" onPress={handleLogin} color="#4CAF50" />
    </ScrollView>
  );
}

// Homepage
function Homepage({ navigation }) {
  const [weather, setWeather] = useState(null);
  const [callNumber, setCallNumber] = useState('555-123-4567');
  const operator = localStorage.getItem('operator');

  useEffect(() => {
    navigator.geolocation.getCurrentPosition((position) => {
      axios.get(`https://api.openweathermap.org/data/2.5/weather?lat=${position.coords.latitude}&lon=${position.coords.longitude}&appid=YOUR_API_KEY&units=imperial`)
        .then(response => setWeather({
          temp: Math.round(response.data.main.temp),
          rain: response.data.rain ? response.data.rain['1h'] * 100 || 0 : 0,
          humidity: response.data.main.humidity,
          wind: Math.round(response.data.wind.speed)
        }))
        .catch(error => setWeather({ temp: 85, rain: 10, humidity: 98, wind: 2 }));
      axios.get('https://fastapi-cloud-app-3.onrender.com/settings/call_number')
        .then(response => setCallNumber(response.data.call_number))
        .catch(error => console.error('Failed to load call number'));
    }, () => setWeather({ temp: 85, rain: 10, humidity: 98, wind: 2 }));
  }, []);

  const handleClockOut = () => {
    axios.put(`https://fastapi-cloud-app-3.onrender.com/operators/`, { clock_out: new Date().toISOString() })
      .then(() => Alert.alert('Clocked out!'))
      .catch(() => Alert.alert('Clock out failed'));
  };

  const handleEndOfDay = () => {
    axios.post('https://fastapi-cloud-app-3.onrender.com/end_of_day/', { operator_id: 1 })
      .then(() => navigation.navigate('Home'))
      .catch(() => Alert.alert('End of day failed'));
  };

  return (
    <ScrollView contentContainerStyle={{ padding: 20 }}>
      <Text style={{ fontSize: 20 }}>TICK CONTROL, INC | HOME</Text>
      <Text style={{ fontSize: 16, marginBottom: 10 }}>{operator}</Text>
      <View style={{ backgroundColor: '#4CAF50', padding: 10, marginBottom: 10 }}>
        <Text>{new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</Text>
        {weather && <Text>TEMP: {weather.temp}° RAIN: {weather.rain}% HUM: {weather.humidity}% WIND: {weather.wind}MPH</Text>}
        <Text>WELCOME {operator}. REMEMBER TO CLOCK IN/OUT.</Text>
      </View>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 10 }}>
        <Text>7:00 A.M.</Text>
        <Button title="CLOCK OUT" onPress={handleClockOut} color="#4CAF50" />
      </View>
      <Button title="TODAY'S SCHEDULE" onPress={() => navigation.navigate('TruckSelection')} color="#4CAF50" />
      <Button title="CALENDAR" onPress={() => navigation.navigate('Calendar')} color="#4CAF50" />
      <Button title="HOURS" color="#4CAF50" />
      <Button title="WEATHER" color="#4CAF50" />
      <Button title="TRUCKS" onPress={() => navigation.navigate('TruckMaintenance')} color="#4CAF50" />
      <Button title="CLOSE THE DAY" onPress={handleEndOfDay} color="#4CAF50" />
      <View style={{ flexDirection: 'row', justifyContent: 'space-around', marginTop: 20 }}>
        <Button title="CALL" onPress={() => Linking.openURL(`tel:${callNumber}`)} color="#f44336" />
        <Button title="GAS" onPress={() => navigation.navigate('GasFillUp')} color="#ffca28" />
        <Button title="END OF DAY" onPress={handleEndOfDay} color="#4CAF50" />
        <Button title="HOME" onPress={() => navigation.navigate('Home')} color="#4CAF50" />
        <Button title="⚙️" color="#757575" />
      </View>
    </ScrollView>
  );
}

// Truck Selection
function TruckSelection({ navigation }) {
  const [trucks, setTrucks] = useState([]);
  const operator = localStorage.getItem('operator');

  useEffect(() => {
    axios.get('https://fastapi-cloud-app-3.onrender.com/trucks/')
      .then(response => setTrucks(response.data))
      .catch(error => console.error('Failed to load trucks:', error));
  }, []);

  return (
    <ScrollView contentContainerStyle={{ padding: 20 }}>
      <Text style={{ fontSize: 20 }}>TICK CONTROL, INC | CHOOSE YOUR TRUCK</Text>
      <Text style={{ fontSize: 16, marginBottom: 10 }}>{operator}</Text>
      <View style={{ backgroundColor: '#4CAF50', padding: 10, marginBottom: 10 }}>
        <Text>{new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</Text>
        <Text>TEMP: 85° RAIN: 10% HUM: 98% WIND: 2MPH</Text>
        <Text>WHICH TRUCK ARE YOU IN TODAY?</Text>
      </View>
      <Image source={{ uri: 'https://via.placeholder.com/200x100?text=TRUCK+IMAGE' }} style={{ width: 200, height: 100, marginBottom: 20 }} />
      {trucks.map(truck => (
        <Button key={truck.id} title={truck.name} onPress={() => navigation.navigate('JobList', { truckName: truck.name })} color="#4CAF50" />
      ))}
      <View style={{ flexDirection: 'row', justifyContent: 'space-around', marginTop: 20 }}>
        <Button title="END OF DAY" onPress={() => navigation.navigate('Home')} color="#4CAF50" />
        <Button title="HOME" onPress={() => navigation.navigate('Home')} color="#4CAF50" />
        <Button title="CALENDAR" onPress={() => navigation.navigate('Calendar')} color="#4CAF50" />
      </View>
    </ScrollView>
  );
}

// Job List
function JobList({ navigation, route }) {
  const { truckName } = route.params;
  const [jobs, setJobs] = useState([]);
  const [callNumber, setCallNumber] = useState('555-123-4567');
  const operator = localStorage.getItem('operator');

  useEffect(() => {
    axios.get('https://fastapi-cloud-app-3.onrender.com/jobs/')
      .then(response => setJobs(response.data.filter(job => job.status !== 'COMPLETED')))
      .catch(error => console.error('Failed to load jobs:', error));
    axios.get('https://fastapi-cloud-app-3.onrender.com/settings/call_number')
      .then(response => setCallNumber(response.data.call_number))
      .catch(error => console.error('Failed to load call number'));
  }, [truckName]);

  const updateStatus = (jobId, status, photoUrl = null) => {
    axios.put(`https://fastapi-cloud-app-3.onrender.com/jobs/${jobId}/status`, { status, photo_url: photoUrl })
      .then(() => navigation.goBack())
      .catch(error => Alert.alert('Status update failed: ' + error));
  };

  const pickImage = async (jobId) => {
    let result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 1,
    });
    if (!result.cancelled) {
      updateStatus(jobId, 'PHOTO', result.uri);
    }
  };

  return (
    <ScrollView contentContainerStyle={{ padding: 20 }}>
      <Text style={{ fontSize: 20 }}>TICK CONTROL, INC | TODAY'S SCHEDULE</Text>
      <Text style={{ fontSize: 16, marginBottom: 10 }}>{operator}</Text>
      <View style={{ backgroundColor: '#4CAF50', padding: 10, marginBottom: 10 }}>
        <Text>IN ROUTE TO: {jobs[0]?.address || 'No jobs'}</Text>
      </View>
      {jobs.map(job => (
        <View key={job.id} style={{ marginBottom: 10 }}>
          <Text>{job.customer_name} ({job.phone || 'N/A'}) {job.address}</Text>
          <Text>{job.notes || 'No notes'}</Text>
          <Button title="GO" onPress={() => updateStatus(job.id, 'GO')} color="#4CAF50" />
          <Button title="START" onPress={() => updateStatus(job.id, 'START')} color="#4CAF50" />
          <Button title="STOP" onPress={() => updateStatus(job.id, 'STOP')} color="#4CAF50" />
          <Button title="PHOTO" onPress={() => pickImage(job.id)} color="#4CAF50" />
          <Button title="NOT COMPLETED" onPress={() => updateStatus(job.id, 'NOT COMPLETED')} color="#f44336" />
        </View>
      ))}
      <View style={{ flexDirection: 'row', justifyContent: 'space-around', marginTop: 20 }}>
        <Button title="CALL" onPress={() => Linking.openURL(`tel:${callNumber}`)} color="#f44336" />
        <Button title="GAS" onPress={() => navigation.navigate('GasFillUp')} color="#ffca28" />
        <Button title="END OF DAY" onPress={() => navigation.navigate('Home')} color="#4CAF50" />
        <Button title="HOME" onPress={() => navigation.navigate('Home')} color="#4CAF50" />
      </View>
    </ScrollView>
  );
}

// Calendar
function Calendar({ navigation }) {
  const operator = localStorage.getItem('operator');
  const [calendar, setCalendar] = useState(null);
  const [month, setMonth] = useState(new Date().getMonth());
  const [year, setYear] = useState(new Date().getFullYear());

  useEffect(() => {
    axios.get(`https://fastapi-cloud-app-3.onrender.com/calendar/${new Date(year, month, 1).toLocaleString('default', { month: 'long' }) + ' ' + year}`)
      .then(response => setCalendar(response.data))
      .catch(error => console.error('Failed to load calendar:', error));
  }, [month, year]);

  const months = ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER'];
  const days = Array.from({ length: new Date(year, month + 1, 0).getDate() }, (_, i) => i + 1);

  return (
    <ScrollView contentContainerStyle={{ padding: 20 }}>
      <Text style={{ fontSize: 20 }}>TICK CONTROL, INC | CALENDAR</Text>
      <Text style={{ fontSize: 16, marginBottom: 10 }}>{operator}</Text>
      <View style={{ backgroundColor: '#4CAF50', padding: 10, marginBottom: 10 }}>
        <Text>{calendar?.month_year || 'Loading...'}</Text>
        <Text>{calendar?.jobs_left || 0} JOBS LEFT TO COMPLETE</Text>
      </View>
      <View style={{ flexDirection: 'row', justifyContent: 'space-around', marginBottom: 10 }}>
        <Button title="←" onPress={() => setYear(year - 1)} color="#4CAF50" />
        <Text>{year}</Text>
        <Button title="→" onPress={() => setYear(year + 1)} color="#4CAF50" />
      </View>
      {months.map((m, i) => (
        <Button key={i} title={m} onPress={() => setMonth(i)} color={month === i ? '#4CAF50' : '#ccc'} />
      ))}
      <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
        {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map(day => <Text key={day}>{day}</Text>)}
      </View>
      {Array.from({ length: 7 }, (_, i) => (
        <View key={i} style={{ flexDirection: 'row' }}>
          {days.slice(i * 7, (i + 1) * 7).map(d => <Text key={d}>{d}</Text>)}
        </View>
      ))}
      <View style={{ flexDirection: 'row', justifyContent: 'space-around', marginTop: 20 }}>
        <Button title="HOME" onPress={() => navigation.navigate('Home')} color="#4CAF50" />
        <Button title="CALENDAR" color="#4CAF50" />
      </View>
    </ScrollView>
  );
}

// Truck Maintenance Overview
function TruckMaintenanceOverview({ navigation }) {
  const [trucks, setTrucks] = useState([]);
  const operator = localStorage.getItem('operator');

  useEffect(() => {
    axios.get('https://fastapi-cloud-app-3.onrender.com/trucks/')
      .then(response => setTrucks(response.data))
      .catch(error => console.error('Failed to load trucks:', error));
  }, []);

  return (
    <ScrollView contentContainerStyle={{ padding: 20 }}>
      <Text style={{ fontSize: 20 }}>TICK CONTROL, INC | TRUCK MAINTENANCE</Text>
      <Text style={{ fontSize: 16, marginBottom: 10 }}>{operator}</Text>
      <View style={{ backgroundColor: '#4CAF50', padding: 10, marginBottom: 10 }}>
        <Text>TRUCK MAINTENANCE</Text>
      </View>
      <Image source={{ uri: 'https://via.placeholder.com/200x100?text=TRUCK+IMAGE' }} style={{ width: 200, height: 100, marginBottom: 20 }} />
      {trucks.map(truck => (
        <Button key={truck.id} title={truck.name} onPress={() => navigation.navigate(`TruckMaintenance${truck.name.replace(' ', '')}`)} color="#4CAF50" />
      ))}
      <View style={{ flexDirection: 'row', justifyContent: 'space-around', marginTop: 20 }}>
        <Button title="CHANGE TRUCK" onPress={() => navigation.navigate('TruckMaintenanceOverview')} color="#4CAF50" />
        <Button title="HOME" onPress={() => navigation.navigate('Home')} color="#4CAF50" />
        <Button title="OVERVIEW" color="#4CAF50" />
      </View>
    </ScrollView>
  );
}

// Gas Fill-Up (Example Maintenance Page)
function GasFillUp({ navigation }) {
  const [formData, setFormData] = useState({ diesel_gallons: '', diesel_price: '', regular_gallons: '', regular_price: '', mileage: '' });

  const handleSubmit = () => {
    axios.post('https://fastapi-cloud-app-3.onrender.com/truck_maintenance/', {
      truck_id: 1, // Replace with dynamic truck_id
      maintenance_type: 'Gas Fill-Up',
      mileage: formData.mileage,
      performer: localStorage.getItem('operator')
    }).then(() => navigation.navigate('TruckMaintenanceOverview'))
      .catch(error => Alert.alert('Submit failed: ' + error));
  };

  return (
    <ScrollView contentContainerStyle={{ padding: 20 }}>
      <Text style={{ fontSize: 20 }}>TICK CONTROL, INC | TICK 1 - GAS FILL-UP</Text>
      <Text style={{ fontSize: 16, marginBottom: 10 }}>{localStorage.getItem('operator')}</Text>
      <View style={{ backgroundColor: '#4CAF50', padding: 10, marginBottom: 10 }}>
        <Text>TICK 1 GAS FILL-UP</Text>
      </View>
      <TextInput
        style={{ height: 40, borderColor: 'gray', borderWidth: 1, marginBottom: 10, padding: 10 }}
        placeholder="DIESEL - GALLONS"
        value={formData.diesel_gallons}
        onChangeText={text => setFormData({ ...formData, diesel_gallons: text })}
      />
      <TextInput
        style={{ height: 40, borderColor: 'gray', borderWidth: 1, marginBottom: 10, padding: 10 }}
        placeholder="PRICE PER GALLON"
        value={formData.diesel_price}
        onChangeText={text => setFormData({ ...formData, diesel_price: text })}
      />
      <TextInput
        style={{ height: 40, borderColor: 'gray', borderWidth: 1, marginBottom: 10, padding: 10 }}
        placeholder="REGULAR - GALLONS"
        value={formData.regular_gallons}
        onChangeText={text => setFormData({ ...formData, regular_gallons: text })}
      />
      <TextInput
        style={{ height: 40, borderColor: 'gray', borderWidth: 1, marginBottom: 10, padding: 10 }}
        placeholder="PRICE PER GALLON"
        value={formData.regular_price}
        onChangeText={text => setFormData({ ...formData, regular_price: text })}
      />
      <TextInput
        style={{ height: 40, borderColor: 'gray', borderWidth: 1, marginBottom: 10, padding: 10 }}
        placeholder="MILEAGE"
        value={formData.mileage}
        onChangeText={text => setFormData({ ...formData, mileage: text })}
      />
      <Button title="TICK 1 - SUBMIT" onPress={handleSubmit} color="#4CAF50" />
      <View style={{ flexDirection: 'row', justifyContent: 'space-around', marginTop: 20 }}>
        <Button title="CHANGE TRUCK" onPress={() => navigation.navigate('TruckMaintenanceOverview')} color="#4CAF50" />
        <Button title="HOME" onPress={() => navigation.navigate('Home')} color="#4CAF50" />
        <Button title="OVERVIEW" onPress={() => navigation.navigate('TruckMaintenanceOverview')} color="#4CAF50" />
      </View>
    </ScrollView>
  );
}

// Add Oil Change, Tires, DEF, Emissions, Insurance pages similarly

export default App;

// src/App.css (Updated for React Native)
import { StyleSheet } from 'react-native';

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#fff',
  },
  header: {
    fontSize: 20,
    marginBottom: 10,
  },
  subheader: {
    fontSize: 16,
    marginBottom: 10,
  },
  infoWindow: {
    backgroundColor: '#4CAF50',
    color: 'white',
    padding: 10,
    marginBottom: 10,
  },
  button: {
    marginVertical: 5,
    padding: 10,
  },
  callButton: {
    backgroundColor: '#f44336',
  },
  gasButton: {
    backgroundColor: '#ffca28',
  },
  endOfDayButton: {
    backgroundColor: '#4CAF50',
  },
  homeButton: {
    backgroundColor: '#4CAF50',
  },
  changeTruckButton: {
    backgroundColor: '#4CAF50',
  },
  overviewButton: {
    backgroundColor: '#4CAF50',
  },
  gearButton: {
    backgroundColor: '#757575',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 20,
  },
});

export default styles;
