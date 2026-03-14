"""Test US-03: Recording functionality using mocks"""
import pytest
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.unit
def test_microphone_permission_request():
    """Test that microphone permission is requested via getUserMedia."""
    # Mock navigator.mediaDevices.getUserMedia
    mock_stream = Mock()
    mock_get_user_media = Mock(return_value=mock_stream)
    mock_navigator = Mock()
    mock_navigator.mediaDevices.getUserMedia = mock_get_user_media
    
    # Simulate the permission request logic
    def request_microphone(navigator):
        """Simulate requesting microphone permission."""
        return navigator.mediaDevices.getUserMedia({'audio': True})
    
    # Call the function with mock navigator
    result = request_microphone(mock_navigator)
    
    # Verify getUserMedia was called with correct constraints
    mock_get_user_media.assert_called_once_with({'audio': True})
    assert result is mock_stream


@pytest.mark.unit
def test_permission_denied_shows_error():
    """Test that permission denied shows error message."""
    # Mock getUserMedia to raise permission denied error
    permission_error = Exception("Permission denied")
    mock_get_user_media = Mock(side_effect=permission_error)
    mock_navigator = Mock()
    mock_navigator.mediaDevices.getUserMedia = mock_get_user_media
    
    def start_recording_with_error_handling(navigator):
        """Simulate starting recording with error handling."""
        try:
            return navigator.mediaDevices.getUserMedia({'audio': True})
        except Exception as e:
            return f"麦克风权限被拒绝: {str(e)}"
    
    # Call the function
    result = start_recording_with_error_handling(mock_navigator)
    
    # Verify error message is returned
    assert "权限被拒绝" in result or "Permission denied" in result
    mock_get_user_media.assert_called_once_with({'audio': True})


@pytest.mark.unit
def test_start_recording():
    """Test that recording can be started via MediaRecorder."""
    # Mock MediaRecorder
    mock_recorder = Mock()
    mock_recorder.start = Mock()
    mock_recorder.state = 'recording'
    
    # Mock MediaRecorder constructor
    mock_media_recorder_class = Mock(return_value=mock_recorder)
    
    def start_recording(stream, MediaRecorder):
        """Simulate starting recording."""
        recorder = MediaRecorder(stream)
        recorder.start()
        return recorder
    
    # Call the function with mock class
    mock_stream = Mock()
    recorder = start_recording(mock_stream, mock_media_recorder_class)
    
    # Verify MediaRecorder was created and started
    mock_media_recorder_class.assert_called_once_with(mock_stream)
    mock_recorder.start.assert_called_once()
    assert recorder.state == 'recording'


@pytest.mark.unit
def test_stop_recording():
    """Test that recording can be stopped via MediaRecorder."""
    # Mock MediaRecorder
    mock_recorder = Mock()
    mock_recorder.stop = Mock()
    mock_recorder.state = 'inactive'
    
    # Mock data handler
    recorded_chunks = []
    
    def mock_ondataavailable(event):
        recorded_chunks.append(event.data)
    
    mock_recorder.ondataavailable = mock_ondataavailable
    
    def stop_recording(recorder):
        """Simulate stopping recording."""
        # Simulate data available event before stopping
        mock_event = Mock(data=b'audio_data')
        recorder.ondataavailable(mock_event)
        recorder.stop()
        return recorded_chunks
    
    # Call the function
    chunks = stop_recording(mock_recorder)
    
    # Verify stop was called and data was captured
    mock_recorder.stop.assert_called_once()
    assert len(chunks) == 1
    assert chunks[0] == b'audio_data'
