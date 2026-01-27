"""VideoPlayer 클래스 테스트"""
import pytest
import numpy as np
import os
import cv2


class TestVideoPlayer:
    """VideoPlayer 클래스 테스트"""

    @pytest.fixture
    def player(self):
        from src.core.video_player import VideoPlayer
        p = VideoPlayer()
        yield p
        p.release()

    @pytest.fixture
    def sample_video_path(self, tmp_path):
        """테스트용 비디오 생성"""
        video_path = tmp_path / "test_video.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, 30, (640, 480))

        for i in range(90):  # 3초 분량 (30fps)
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, f'Frame {i}', (50, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)
            out.write(frame)

        out.release()
        return str(video_path)

    # --- 비디오 로드 ---

    def test_load_video_success(self, player, sample_video_path):
        """비디오 로드 성공 테스트"""
        result = player.load(sample_video_path)
        assert result == True
        assert player.is_loaded == True

    def test_load_video_file_not_found(self, player):
        """존재하지 않는 파일 로드 테스트"""
        result = player.load('nonexistent.mp4')
        assert result == False
        assert player.is_loaded == False

    def test_load_video_invalid_format(self, player, tmp_path):
        """잘못된 형식 파일 로드 테스트"""
        # 텍스트 파일 생성
        text_file = tmp_path / "test.txt"
        text_file.write_text("not a video")
        result = player.load(str(text_file))
        assert result == False

    # --- 비디오 정보 ---

    def test_get_fps(self, player, sample_video_path):
        """FPS 정보 가져오기 테스트"""
        player.load(sample_video_path)
        fps = player.fps
        assert fps > 0 and fps < 120
        assert abs(fps - 30) < 1  # 30fps로 생성했으므로

    def test_get_frame_count(self, player, sample_video_path):
        """총 프레임 수 가져오기 테스트"""
        player.load(sample_video_path)
        assert player.frame_count == 90  # 90프레임 생성

    def test_get_duration(self, player, sample_video_path):
        """재생 시간 가져오기 테스트"""
        player.load(sample_video_path)
        assert player.duration > 0
        assert abs(player.duration - 3.0) < 0.5  # 약 3초

    def test_get_size(self, player, sample_video_path):
        """비디오 크기 가져오기 테스트"""
        player.load(sample_video_path)
        width, height = player.size
        assert width == 640
        assert height == 480

    # --- 프레임 읽기 ---

    def test_read_frame(self, player, sample_video_path):
        """프레임 읽기 테스트"""
        player.load(sample_video_path)
        frame = player.read_frame()
        assert frame is not None
        assert isinstance(frame, np.ndarray)
        assert frame.shape == (480, 640, 3)

    def test_read_frame_when_not_loaded(self, player):
        """로드 안 된 상태에서 프레임 읽기 테스트"""
        frame = player.read_frame()
        assert frame is None

    def test_read_multiple_frames(self, player, sample_video_path):
        """여러 프레임 순차 읽기 테스트"""
        player.load(sample_video_path)
        for i in range(10):
            frame = player.read_frame()
            assert frame is not None
            assert player.current_frame == i + 1

    # --- 시크 ---

    def test_seek_to_position(self, player, sample_video_path):
        """특정 위치로 시크 테스트"""
        player.load(sample_video_path)
        target_frame = 50
        player.seek(target_frame)
        assert player.current_frame == target_frame

    def test_seek_to_invalid_position_negative(self, player, sample_video_path):
        """음수 위치로 시크 테스트"""
        player.load(sample_video_path)
        player.seek(-1)
        assert player.current_frame >= 0

    def test_seek_to_invalid_position_overflow(self, player, sample_video_path):
        """프레임 수 초과 위치로 시크 테스트"""
        player.load(sample_video_path)
        player.seek(1000)  # 90프레임인데 1000으로 시크
        assert player.current_frame <= player.frame_count

    # --- 재생 상태 ---

    def test_play_pause(self, player, sample_video_path):
        """재생/일시정지 토글 테스트"""
        player.load(sample_video_path)
        assert player.is_playing == False
        player.play()
        assert player.is_playing == True
        player.pause()
        assert player.is_playing == False

    def test_stop(self, player, sample_video_path):
        """정지 테스트"""
        player.load(sample_video_path)
        player.seek(50)
        player.play()
        player.stop()
        assert player.is_playing == False
        assert player.current_frame == 0

    # --- 리소스 해제 ---

    def test_release(self, player, sample_video_path):
        """리소스 해제 테스트"""
        player.load(sample_video_path)
        player.release()
        assert player.is_loaded == False
