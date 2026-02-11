"""분석 결과 탭 위젯 - 신체 부위별 움직임 빈도 분석 결과 표시"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QStackedWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QAbstractItemView,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from src.core.movement_analyzer import MovementAnalysisResult, BodyPartStats
from src.ui.bar_item_delegate import BarItemDelegate, get_risk_color
from src.ui.components.license_overlay import LicenseOverlay
from src.license import LicenseManager


# 테이블 컬럼 인덱스
COL_BODY_PART = 0
COL_MOVEMENT = 1
COL_RISK = 2
COL_AVG_ANGLE = 3

# 색상 코드 이모지
RISK_EMOJI = {
    'red': '\U0001f534',      # 🔴
    'orange': '\U0001f7e0',   # 🟠
    'yellow': '\U0001f7e1',   # 🟡
    'green': '\U0001f7e2',    # 🟢
}


def _risk_emoji(ratio: float) -> str:
    if ratio >= 0.6:
        return RISK_EMOJI['red']
    elif ratio >= 0.4:
        return RISK_EMOJI['orange']
    elif ratio >= 0.2:
        return RISK_EMOJI['yellow']
    else:
        return RISK_EMOJI['green']


class MovementAnalysisWidget(QWidget):
    """분석 결과 탭 위젯 (3가지 상태: 미로드 / 분석 전 / 완료)"""

    analysis_requested = pyqtSignal(int)  # sample_interval

    # 상태 인덱스
    STATE_NO_VIDEO = 0
    STATE_READY = 1
    STATE_RESULT = 2

    # 라이센스 등록 요청 시그널
    register_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._result: MovementAnalysisResult = None
        self._total_frames: int = 0
        self._video_path: str = None
        self._resume_data: dict = None  # 재개용 상태 저장
        self._init_ui()
        self._apply_style()
        self._setup_license_overlay()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._stacked = QStackedWidget()
        layout.addWidget(self._stacked)

        # 상태 0: 동영상 미로드
        self._stacked.addWidget(self._create_no_video_page())

        # 상태 1: 분석 전 (동영상 로드됨)
        self._stacked.addWidget(self._create_ready_page())

        # 상태 2: 분석 완료
        self._stacked.addWidget(self._create_result_page())

        self._stacked.setCurrentIndex(self.STATE_NO_VIDEO)

    def _create_no_video_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel("동영상을 먼저 로드해주세요.")
        label.setObjectName("infoLabel")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        btn = QPushButton("분석 시작")
        btn.setObjectName("analysisButton")
        btn.setFixedSize(140, 36)
        btn.setEnabled(False)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        return page

    def _create_ready_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        layout.addStretch()

        # 안내 문구
        info_label = QLabel(
            "신체 부위별 움직임 빈도를 분석합니다.\n"
            "동영상 전체를 순차 스캔하여 각 관절의 움직임 횟수와\n"
            "고위험 자세 노출 비율을 계산합니다."
        )
        info_label.setObjectName("infoLabel")
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        # 샘플링 옵션
        sampling_layout = QHBoxLayout()
        sampling_layout.addStretch()
        sampling_label = QLabel("프레임 샘플링:")
        sampling_label.setObjectName("optionLabel")
        sampling_layout.addWidget(sampling_label)

        self._sampling_combo = QComboBox()
        self._sampling_combo.addItem("전체 프레임", 1)
        self._sampling_combo.addItem("매 2프레임", 2)
        self._sampling_combo.addItem("매 3프레임", 3)
        self._sampling_combo.setCurrentIndex(1)  # 매 2프레임 기본 선택
        self._sampling_combo.setFixedWidth(160)
        self._sampling_combo.currentIndexChanged.connect(self._on_sampling_changed)
        sampling_layout.addWidget(self._sampling_combo)
        sampling_layout.addStretch()
        layout.addLayout(sampling_layout)

        # 예상 프레임 수
        self._expected_label = QLabel("예상 분석 대상: - 프레임")
        self._expected_label.setObjectName("expectedLabel")
        self._expected_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._expected_label)

        # 재개 진행률 라벨
        self._resume_label = QLabel()
        self._resume_label.setObjectName("expectedLabel")
        self._resume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._resume_label.setVisible(False)
        layout.addWidget(self._resume_label)

        # 분석 시작/재개 버튼
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._start_btn = QPushButton("분석 시작")
        self._start_btn.setObjectName("analysisButton")
        self._start_btn.setFixedSize(140, 36)
        self._start_btn.clicked.connect(self._on_start_clicked)
        btn_layout.addWidget(self._start_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 처음부터 시작 버튼 (재개 상태일 때만 표시)
        restart_layout = QHBoxLayout()
        restart_layout.addStretch()
        self._restart_btn = QPushButton("처음부터 시작")
        self._restart_btn.setObjectName("restartButton")
        self._restart_btn.setFixedSize(140, 30)
        self._restart_btn.clicked.connect(self._on_restart_clicked)
        self._restart_btn.setVisible(False)
        restart_layout.addWidget(self._restart_btn)
        restart_layout.addStretch()
        layout.addLayout(restart_layout)

        layout.addStretch()

        return page

    def _create_result_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 경고 배너 (감지 실패율 >30%)
        self._warning_banner = QLabel()
        self._warning_banner.setObjectName("warningBanner")
        self._warning_banner.setWordWrap(True)
        self._warning_banner.setVisible(False)
        layout.addWidget(self._warning_banner)

        # 요약 정보
        self._summary_label = QLabel()
        self._summary_label.setObjectName("summaryLabel")
        self._summary_label.setWordWrap(True)
        layout.addWidget(self._summary_label)

        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("separator")
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        # 결과 테이블
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["부위", "움직임", "고위험 비율", "평균 각도"])
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(False)
        self._table.verticalHeader().setVisible(False)
        self._table.setSortingEnabled(True)

        # 컬럼 헤더 크기
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(COL_BODY_PART, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_MOVEMENT, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_RISK, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_AVG_ANGLE, QHeaderView.ResizeMode.ResizeToContents)

        # 인라인 바 델리게이트
        self._bar_delegate = BarItemDelegate(self._table)
        self._table.setItemDelegateForColumn(COL_MOVEMENT, self._bar_delegate)
        self._table.setItemDelegateForColumn(COL_RISK, self._bar_delegate)

        layout.addWidget(self._table)

        # 다시 분석 버튼
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._retry_btn = QPushButton("다시 분석")
        self._retry_btn.setObjectName("analysisButton")
        self._retry_btn.setFixedSize(140, 36)
        self._retry_btn.clicked.connect(self._on_retry_clicked)
        btn_layout.addWidget(self._retry_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return page

    def _apply_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QLabel#infoLabel {
                font-size: 13px;
                color: #aaaaaa;
                padding: 8px;
            }
            QLabel#optionLabel {
                font-size: 12px;
                color: #cccccc;
            }
            QLabel#expectedLabel {
                font-size: 12px;
                color: #888888;
                padding-left: 4px;
            }
            QLabel#summaryLabel {
                font-size: 12px;
                color: #cccccc;
                padding: 4px;
            }
            QLabel#warningBanner {
                background-color: #5a3a2a;
                color: #ffaa66;
                border: 1px solid #8a5a3a;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            QFrame#separator {
                background-color: #3a3a3a;
            }
            QPushButton#analysisButton {
                background-color: #4a9eff;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 6px 16px;
            }
            QPushButton#analysisButton:hover {
                background-color: #5aaeFF;
            }
            QPushButton#analysisButton:pressed {
                background-color: #3a8eef;
            }
            QPushButton#analysisButton:disabled {
                background-color: #444444;
                color: #666666;
            }
            QPushButton#restartButton {
                background-color: transparent;
                color: #888888;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                font-size: 11px;
                padding: 4px 12px;
            }
            QPushButton#restartButton:hover {
                color: #aaaaaa;
                border-color: #5a5a5a;
            }
            QComboBox {
                background-color: #2a2a2a;
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #2a2a2a;
                color: #e0e0e0;
                selection-background-color: #4a9eff;
                border: 1px solid #3a3a3a;
            }
            QTableWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
                gridline-color: #2a2a2a;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 4px;
                border-bottom: 1px solid #2a2a2a;
            }
            QTableWidget::item:selected {
                background-color: #32324a;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #cccccc;
                border: none;
                border-bottom: 1px solid #3a3a3a;
                border-right: 1px solid #3a3a3a;
                padding: 6px 8px;
                font-size: 11px;
                font-weight: bold;
            }
        """)

    def _setup_license_overlay(self):
        """라이센스 오버레이 설정"""
        self._license_overlay = LicenseOverlay(self, feature_name="움직임 빈도 분석")
        self._license_overlay.register_clicked.connect(
            lambda: self.register_requested.emit()
        )

        # 라이센스 상태에 따라 오버레이 표시/숨김
        license_manager = LicenseManager.instance()
        license_manager.license_changed.connect(self._update_license_overlay)
        self._update_license_overlay()

    def _update_license_overlay(self):
        """라이센스 상태에 따라 오버레이 표시/숨김"""
        is_licensed = LicenseManager.instance().is_licensed
        if is_licensed:
            self._license_overlay.hide()
        else:
            self._license_overlay.show()
            self._license_overlay.raise_()

    # === 공개 API ===

    def set_video_info(self, video_path: str, total_frames: int):
        """동영상 로드 시 호출 - 분석 전 상태로 전환"""
        if video_path != self._video_path:
            self._resume_data = None  # 다른 동영상이면 재개 상태 초기화
        self._video_path = video_path
        self._total_frames = total_frames
        self._result = None
        self._update_expected_frames()
        self._update_resume_ui()
        self._stacked.setCurrentIndex(self.STATE_READY)

    def clear_video(self):
        """동영상 해제 시 - 미로드 상태로 전환"""
        self._video_path = None
        self._total_frames = 0
        self._result = None
        self._resume_data = None
        self._stacked.setCurrentIndex(self.STATE_NO_VIDEO)

    def reset_to_ready(self):
        """새 동영상 로드 시 - 기존 결과 제거 후 분석 전 상태"""
        self._result = None
        self._resume_data = None
        self._update_resume_ui()
        if self._video_path:
            self._stacked.setCurrentIndex(self.STATE_READY)
        else:
            self._stacked.setCurrentIndex(self.STATE_NO_VIDEO)

    def save_resume_state(self, partial_state: dict):
        """취소 시 재개 상태 저장"""
        self._resume_data = partial_state
        self._update_resume_ui()
        self._stacked.setCurrentIndex(self.STATE_READY)

    def get_resume_data(self) -> dict:
        """재개 데이터 반환"""
        return self._resume_data

    def set_result(self, result: MovementAnalysisResult, video_missing: bool = False):
        """분석 결과 설정 - 결과 화면으로 전환

        Args:
            result: 분석 결과
            video_missing: 동영상 파일 누락 여부 (프로젝트 로드 시)
        """
        self._result = result
        self._resume_data = None  # 분석 완료 시 재개 상태 초기화
        self._populate_result(video_missing=video_missing)
        self._stacked.setCurrentIndex(self.STATE_RESULT)

    def get_result(self) -> MovementAnalysisResult:
        """현재 분석 결과 반환"""
        return self._result

    def get_sample_interval(self) -> int:
        """선택된 샘플링 간격 반환"""
        return self._sampling_combo.currentData()

    # === 내부 메서드 ===

    def _on_sampling_changed(self, index: int):
        self._update_expected_frames()

    def _update_expected_frames(self):
        if self._total_frames <= 0:
            self._expected_label.setText("예상 분석 대상: - 프레임")
            return
        interval = self._sampling_combo.currentData()
        expected = self._total_frames // interval
        self._expected_label.setText(f"예상 분석 대상: {expected:,} 프레임")

    def _on_start_clicked(self):
        interval = self._sampling_combo.currentData()
        self._sampling_combo.setEnabled(False)
        self.analysis_requested.emit(interval)

    def _on_retry_clicked(self):
        """다시 분석 클릭 - 초기화 후 옵션 선택 화면으로"""
        self._result = None
        self._resume_data = None
        self._sampling_combo.setEnabled(True)
        self._update_resume_ui()
        self._stacked.setCurrentIndex(self.STATE_READY)

    def _on_restart_clicked(self):
        """처음부터 시작 클릭 - 샘플링 옵션 잠금 해제"""
        self._resume_data = None
        self._sampling_combo.setEnabled(True)
        self._update_resume_ui()
        interval = self._sampling_combo.currentData()
        self.analysis_requested.emit(interval)

    def _update_resume_ui(self):
        """재개 상태에 따라 버튼 텍스트 업데이트"""
        if self._resume_data and self._total_frames > 0:
            frame_index = self._resume_data.get('frame_index', 0)
            progress = frame_index / self._total_frames * 100
            self._start_btn.setText(f"분석 재개 ({progress:.0f}%)")
            self._resume_label.setText(
                f"이전 진행: {frame_index:,} / {self._total_frames:,} 프레임"
            )
            self._resume_label.setVisible(True)
            self._restart_btn.setVisible(True)
            self._sampling_combo.setEnabled(False)
        else:
            self._start_btn.setText("분석 시작")
            self._resume_label.setVisible(False)
            self._restart_btn.setVisible(False)
            self._sampling_combo.setEnabled(True)

    def _populate_result(self, video_missing: bool = False):
        """결과 데이터를 테이블에 채우기"""
        result = self._result
        if not result:
            return

        # 경고 배너
        warnings = []
        total_analyzed_attempted = result.analyzed_frames + result.skipped_frames
        if total_analyzed_attempted > 0:
            fail_rate = result.skipped_frames / total_analyzed_attempted
        else:
            fail_rate = 0.0

        if video_missing:
            warnings.append(
                "⚠ 동영상 파일이 변경되었거나 찾을 수 없습니다. "
                "다시 분석을 권장합니다."
            )

        if fail_rate > 0.3:
            warnings.append(
                f"⚠ 감지 실패율이 높습니다: {fail_rate:.1%} ({result.skipped_frames}프레임 실패)\n"
                "화질이 낮거나 사람이 가려진 구간이 많을 수 있습니다."
            )

        if warnings:
            self._warning_banner.setText("\n".join(warnings))
            self._warning_banner.setVisible(True)
        else:
            self._warning_banner.setVisible(False)

        # 요약 정보
        success_rate = 1.0 - fail_rate
        self._summary_label.setText(
            f"분석 프레임: {result.analyzed_frames:,}  |  "
            f"소요 시간: {result.duration_seconds:.1f}초  |  "
            f"감지 성공률: {success_rate:.1%}  |  "
            f"샘플링: {'전체' if result.sample_interval == 1 else f'매 {result.sample_interval}프레임'}"
        )

        # 테이블 데이터
        body_parts = list(result.body_parts.values())
        max_movement = max((bp.movement_count for bp in body_parts), default=1) or 1

        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(body_parts))

        for row, bp in enumerate(sorted(body_parts, key=lambda x: x.movement_count, reverse=True)):
            # 부위명
            name_item = QTableWidgetItem(bp.display_name)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, COL_BODY_PART, name_item)

            # 움직임 바 + 횟수
            movement_item = QTableWidgetItem()
            movement_item.setData(Qt.ItemDataRole.UserRole, {
                'type': 'movement',
                'value': float(bp.movement_count),
                'max_value': float(max_movement),
                'display': str(bp.movement_count),
            })
            # 정렬용 데이터
            movement_item.setData(Qt.ItemDataRole.DisplayRole, bp.movement_count)
            self._table.setItem(row, COL_MOVEMENT, movement_item)

            # 고위험 비율 바 + %
            risk_item = QTableWidgetItem()
            risk_item.setData(Qt.ItemDataRole.UserRole, {
                'type': 'risk',
                'value': bp.high_risk_ratio,
                'max_value': 1.0,
                'display': f"{bp.high_risk_ratio:.1%} {_risk_emoji(bp.high_risk_ratio)}",
            })
            risk_item.setData(Qt.ItemDataRole.DisplayRole, bp.high_risk_ratio)
            self._table.setItem(row, COL_RISK, risk_item)

            # 평균 각도
            angle_item = QTableWidgetItem(f"{bp.avg_angle:.1f}°")
            angle_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            angle_item.setData(Qt.ItemDataRole.DisplayRole, bp.avg_angle)
            self._table.setItem(row, COL_AVG_ANGLE, angle_item)

        self._table.setSortingEnabled(True)
        self._table.setRowCount(len(body_parts))
