guard HandTrackingProvider.isSupported else {
  throw HandTrackingServiceError.unsupported
}

var authorization =
  await session.queryAuthorization(for: [.handTracking])[.handTracking]
  ?? .notDetermined

if authorization == .notDetermined {
  authorization =
    await session.requestAuthorization(for: [.handTracking])[.handTracking]
    ?? .denied
}

guard authorization == .allowed else {
  throw HandTrackingServiceError.authorizationDenied
}

try await session.run([provider])
