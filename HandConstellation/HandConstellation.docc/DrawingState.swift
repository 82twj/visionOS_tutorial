enum DrawingState: Equatable {
    case disabled
    case enabled
}

var drawingState: DrawingState = .disabled

var isDrawingEnabled: Bool {
    drawingState == .enabled
}

func toggleDrawing() {
    drawingState = isDrawingEnabled ? .disabled : .enabled
}
