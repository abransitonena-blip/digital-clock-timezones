import { create } from 'zustand'

const useClockStore = create((set) => ({
  // Alarmas
  alarms: JSON.parse(localStorage.getItem('alarms')) || [],
  addAlarm: (alarm) => set((state) => {
    const newAlarms = [...state.alarms, { ...alarm, id: Date.now() }]
    localStorage.setItem('alarms', JSON.stringify(newAlarms))
    return { alarms: newAlarms }
  }),
  deleteAlarm: (id) => set((state) => {
    const newAlarms = state.alarms.filter(a => a.id !== id)
    localStorage.setItem('alarms', JSON.stringify(newAlarms))
    return { alarms: newAlarms }
  }),
  toggleAlarm: (id) => set((state) => {
    const newAlarms = state.alarms.map(a => a.id === id ? { ...a, enabled: !a.enabled } : a)
    localStorage.setItem('alarms', JSON.stringify(newAlarms))
    return { alarms: newAlarms }
  }),

  // Tema
  theme: JSON.parse(localStorage.getItem('theme')) || {
    name: 'purple',
    primaryColor: '#667eea',
    secondaryColor: '#764ba2',
    backgroundColor: '#0f0f0f'
  },
  setTheme: (theme) => set(() => {
    localStorage.setItem('theme', JSON.stringify(theme))
    return { theme }
  }),

  // Sonido
  soundEnabled: JSON.parse(localStorage.getItem('soundEnabled')) !== false,
  toggleSound: () => set((state) => {
    localStorage.setItem('soundEnabled', JSON.stringify(!state.soundEnabled))
    return { soundEnabled: !state.soundEnabled }
  }),

  // Zonas horarias
  timezones: JSON.parse(localStorage.getItem('timezones')) || [
    { id: 'America/Mexico_City', city: 'México City', offset: -6 },
    { id: 'America/New_York', city: 'Nueva York', offset: -5 },
    { id: 'Europe/London', city: 'Londres', offset: 0 },
    { id: 'Europe/Paris', city: 'París', offset: 1 },
    { id: 'Asia/Tokyo', city: 'Tokio', offset: 9 },
    { id: 'Asia/Dubai', city: 'Dubai', offset: 4 },
    { id: 'Australia/Sydney', city: 'Sydney', offset: 11 },
    { id: 'Asia/Bangkok', city: 'Bangkok', offset: 7 },
    { id: 'America/Los_Angeles', city: 'Los Ángeles', offset: -8 },
    { id: 'Asia/Singapore', city: 'Singapur', offset: 8 },
    { id: 'America/Toronto', city: 'Toronto', offset: -5 },
    { id: 'Europe/Berlin', city: 'Berlín', offset: 1 }
  ],
  addTimezone: (tz) => set((state) => {
    const newTz = [...state.timezones, tz]
    localStorage.setItem('timezones', JSON.stringify(newTz))
    return { timezones: newTz }
  }),
  removeTimezone: (id) => set((state) => {
    const newTz = state.timezones.filter(t => t.id !== id)
    localStorage.setItem('timezones', JSON.stringify(newTz))
    return { timezones: newTz }
  })
}))

export default useClockStore
