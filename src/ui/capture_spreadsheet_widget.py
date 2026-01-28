"""
캡처 스프레드시트 위젯

캡처된 인체공학적 평가 결과를 스프레드시트 형태로 표시.
수동 입력 컬럼 편집 및 자동 재계산 기능 포함.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMenu, QMessageBox, QFileDialog,
    QSpinBox, QStyledItemDelegate,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QAction
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from ..core.capture_model import CaptureRecord, CaptureDataModel


# =============================================================================
# 컬럼 정의
# =============================================================================

# 컬럼 정보: (필드명, 헤더, 그룹, 편집가능, 값범위)
COLUMN_DEFINITIONS = [
    # 기본 정보 (3개)
    ('timestamp', 'Time', 'info', False, None),
    ('frame_number', 'Frame', 'info', False, None),
    ('capture_time', 'Captured', 'info', False, None),

    # RULA 부위 (7개)
    ('rula_upper_arm', 'Upper Arm', 'rula_body', False, None),
    ('rula_lower_arm', 'Lower Arm', 'rula_body', False, None),
    ('rula_wrist', 'Wrist', 'rula_body', False, None),
    ('rula_wrist_twist', 'Wrist Twist', 'rula_body', False, None),
    ('rula_neck', 'Neck', 'rula_body', False, None),
    ('rula_trunk', 'Trunk', 'rula_body', False, None),
    ('rula_leg', 'Leg', 'rula_body', False, None),

    # RULA 수동 입력 (4개)
    ('rula_muscle_use_a', 'Muscle A', 'rula_manual', True, (0, 1)),
    ('rula_force_load_a', 'Force A', 'rula_manual', True, (0, 3)),
    ('rula_muscle_use_b', 'Muscle B', 'rula_manual', True, (0, 1)),
    ('rula_force_load_b', 'Force B', 'rula_manual', True, (0, 3)),

    # RULA 결과 (4개)
    ('rula_score_a', 'Score A', 'rula_result', False, None),
    ('rula_score_b', 'Score B', 'rula_result', False, None),
    ('rula_score', 'Score', 'rula_result', False, None),
    ('rula_risk', 'Risk', 'rula_result', False, None),

    # REBA 부위 (6개)
    ('reba_neck', 'Neck', 'reba_body', False, None),
    ('reba_trunk', 'Trunk', 'reba_body', False, None),
    ('reba_leg', 'Leg', 'reba_body', False, None),
    ('reba_upper_arm', 'Upper Arm', 'reba_body', False, None),
    ('reba_lower_arm', 'Lower Arm', 'reba_body', False, None),
    ('reba_wrist', 'Wrist', 'reba_body', False, None),

    # REBA 수동 입력 (3개)
    ('reba_load_force', 'Load', 'reba_manual', True, (0, 3)),
    ('reba_coupling', 'Coupling', 'reba_manual', True, (0, 3)),
    ('reba_activity', 'Activity', 'reba_manual', True, (0, 3)),

    # REBA 결과 (4개)
    ('reba_score_a', 'Score A', 'reba_result', False, None),
    ('reba_score_b', 'Score B', 'reba_result', False, None),
    ('reba_score', 'Score', 'reba_result', False, None),
    ('reba_risk', 'Risk', 'reba_result', False, None),

    # OWAS 부위 (3개)
    ('owas_back', 'Back', 'owas_body', False, None),
    ('owas_arms', 'Arms', 'owas_body', False, None),
    ('owas_legs', 'Legs', 'owas_body', False, None),

    # OWAS 수동 입력 (1개)
    ('owas_load', 'Load', 'owas_manual', True, (1, 3)),

    # OWAS 결과 (3개)
    ('owas_code', 'Code', 'owas_result', False, None),
    ('owas_ac', 'AC', 'owas_result', False, None),
    ('owas_risk', 'Risk', 'owas_result', False, None),
]

# 그룹별 색상
GROUP_COLORS = {
    'info': QColor(128, 128, 128),      # 회색
    'rula_body': QColor(70, 130, 180),  # 파랑
    'rula_manual': QColor(255, 255, 150),  # 노랑
    'rula_result': QColor(100, 149, 237),  # 연파랑
    'reba_body': QColor(60, 179, 113),  # 초록
    'reba_manual': QColor(255, 255, 150),  # 노랑
    'reba_result': QColor(144, 238, 144),  # 연초록
    'owas_body': QColor(255, 165, 0),   # 주황
    'owas_manual': QColor(255, 255, 150),  # 노랑
    'owas_result': QColor(255, 200, 100),  # 연주황
}

# 위험 수준별 색상
RISK_COLORS = {
    # RULA
    'acceptable': QColor(144, 238, 144),  # 연초록
    'investigate': QColor(255, 255, 150),  # 노랑
    'change_soon': QColor(255, 165, 0),   # 주황
    'change_now': QColor(255, 99, 71),    # 빨강
    # REBA
    'negligible': QColor(144, 238, 144),
    'low': QColor(200, 255, 200),
    'medium': QColor(255, 255, 150),
    'high': QColor(255, 165, 0),
    'very_high': QColor(255, 99, 71),
    # OWAS
    'normal': QColor(144, 238, 144),
    'slight': QColor(255, 255, 150),
    'harmful': QColor(255, 165, 0),
    'very_harmful': QColor(255, 99, 71),
}


class SpinBoxDelegate(QStyledItemDelegate):
    """SpinBox 에디터를 제공하는 Delegate"""

    def __init__(self, min_val: int, max_val: int, parent=None):
        super().__init__(parent)
        self._min_val = min_val
        self._max_val = max_val

    def createEditor(self, parent, option, index):
        editor = QSpinBox(parent)
        editor.setMinimum(self._min_val)
        editor.setMaximum(self._max_val)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        try:
            editor.setValue(int(value) if value else 0)
        except (ValueError, TypeError):
            editor.setValue(self._min_val)

    def setModelData(self, editor, model, index):
        model.setData(index, str(editor.value()), Qt.ItemDataRole.EditRole)


class CaptureSpreadsheetWidget(QWidget):
    """캡처 스프레드시트 위젯"""

    # 시그널
    record_updated = pyqtSignal(int)  # 레코드 업데이트 시 행 인덱스 전달
    export_requested = pyqtSignal(str)  # 내보내기 요청 (파일 경로)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = CaptureDataModel()
        self._updating = False  # 재계산 중 무한 루프 방지

        self._init_ui()
        self._setup_delegates()

    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 테이블 위젯
        self._table = QTableWidget()
        self._table.setColumnCount(len(COLUMN_DEFINITIONS))

        # 헤더 설정
        headers = [col[1] for col in COLUMN_DEFINITIONS]
        self._table.setHorizontalHeaderLabels(headers)

        # 헤더 스타일
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)

        # 선택 모드
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        # 컨텍스트 메뉴
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)

        # 셀 변경 시그널
        self._table.cellChanged.connect(self._on_cell_changed)

        layout.addWidget(self._table)

        # 버튼 영역
        btn_layout = QHBoxLayout()

        self._json_btn = QPushButton("JSON 내보내기")
        self._json_btn.clicked.connect(self._export_json)
        btn_layout.addWidget(self._json_btn)

        self._excel_btn = QPushButton("Excel 내보내기")
        self._excel_btn.clicked.connect(self._export_excel)
        btn_layout.addWidget(self._excel_btn)

        btn_layout.addStretch()

        self._clear_btn = QPushButton("전체 삭제")
        self._clear_btn.clicked.connect(self._clear_all)
        btn_layout.addWidget(self._clear_btn)

        layout.addLayout(btn_layout)

        # 헤더 배경색 설정
        self._apply_header_colors()

    def _setup_delegates(self):
        """수동 입력 컬럼에 SpinBox delegate 설정"""
        for col_idx, (field, header, group, editable, value_range) in enumerate(COLUMN_DEFINITIONS):
            if editable and value_range:
                min_val, max_val = value_range
                delegate = SpinBoxDelegate(min_val, max_val, self._table)
                self._table.setItemDelegateForColumn(col_idx, delegate)

    def _apply_header_colors(self):
        """헤더 배경색 적용"""
        for col_idx, (field, header, group, editable, value_range) in enumerate(COLUMN_DEFINITIONS):
            color = GROUP_COLORS.get(group, QColor(200, 200, 200))
            item = QTableWidgetItem(header)
            item.setBackground(QBrush(color))
            self._table.setHorizontalHeaderItem(col_idx, item)

    def add_record(self, record: CaptureRecord) -> int:
        """
        레코드 추가

        Args:
            record: 추가할 레코드

        Returns:
            삽입된 행 인덱스
        """
        self._updating = True

        # 모델에 추가
        row_idx = self._model.add_record(record)

        # 테이블에 행 추가
        self._table.insertRow(row_idx)
        self._update_row(row_idx)

        self._updating = False
        return row_idx

    def _update_row(self, row: int):
        """행 데이터 업데이트"""
        record = self._model.get_record(row)
        if not record:
            return

        self._updating = True

        for col_idx, (field, header, group, editable, value_range) in enumerate(COLUMN_DEFINITIONS):
            value = getattr(record, field, '')

            # 타임스탬프 포맷팅
            if field == 'timestamp':
                minutes = int(value // 60)
                seconds = value % 60
                value = f"{minutes:02d}:{seconds:06.3f}"
            elif field == 'capture_time' and isinstance(value, datetime):
                value = value.strftime('%H:%M:%S')
            else:
                value = str(value) if value is not None else ''

            item = QTableWidgetItem(value)

            # 읽기 전용 설정
            if not editable:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # 배경색 설정
            color = GROUP_COLORS.get(group, QColor(255, 255, 255))

            # 위험 수준 컬럼은 위험도에 따른 색상
            if field in ('rula_risk', 'reba_risk', 'owas_risk'):
                risk_value = getattr(record, field, '')
                color = RISK_COLORS.get(risk_value, color)

            item.setBackground(QBrush(color))

            # 텍스트 색상 (노랑 배경은 검정 텍스트)
            if group.endswith('_manual'):
                item.setForeground(QBrush(QColor(0, 0, 0)))
            else:
                item.setForeground(QBrush(QColor(0, 0, 0)))

            self._table.setItem(row, col_idx, item)

        self._updating = False

    def _on_cell_changed(self, row: int, col: int):
        """셀 변경 시 재계산"""
        if self._updating:
            return

        field, header, group, editable, value_range = COLUMN_DEFINITIONS[col]
        if not editable:
            return

        record = self._model.get_record(row)
        if not record:
            return

        # 새 값 가져오기
        item = self._table.item(row, col)
        if not item:
            return

        try:
            new_value = int(item.text())
            # 범위 제한
            if value_range:
                new_value = max(value_range[0], min(value_range[1], new_value))
        except ValueError:
            new_value = value_range[0] if value_range else 0

        # 레코드 업데이트
        setattr(record, field, new_value)

        # 재계산
        if group == 'rula_manual':
            record.recalculate_rula()
        elif group == 'reba_manual':
            record.recalculate_reba()
        elif group == 'owas_manual':
            record.recalculate_owas()

        # 모델 업데이트
        self._model.update_record(row, record)

        # UI 갱신
        self._update_row(row)

        # 시그널
        self.record_updated.emit(row)

    def _show_context_menu(self, pos):
        """컨텍스트 메뉴 표시"""
        row = self._table.rowAt(pos.y())
        if row < 0:
            return

        menu = QMenu(self)
        delete_action = QAction("삭제", self)
        delete_action.triggered.connect(lambda: self._delete_row(row))
        menu.addAction(delete_action)

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _delete_row(self, row: int):
        """행 삭제"""
        self._model.delete_record(row)
        self._table.removeRow(row)

    def _clear_all(self):
        """전체 삭제"""
        reply = QMessageBox.question(
            self,
            "확인",
            "모든 캡처 데이터를 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._model.clear()
            self._table.setRowCount(0)

    def _export_json(self):
        """JSON 내보내기"""
        if len(self._model) == 0:
            QMessageBox.warning(self, "경고", "내보낼 데이터가 없습니다.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "JSON 내보내기",
            "",
            "JSON Files (*.json)",
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self._model.to_json())
                QMessageBox.information(self, "완료", f"JSON 파일이 저장되었습니다:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"저장 중 오류 발생:\n{str(e)}")

    def _export_excel(self):
        """Excel 내보내기"""
        if len(self._model) == 0:
            QMessageBox.warning(self, "경고", "내보낼 데이터가 없습니다.")
            return

        try:
            import openpyxl
            from openpyxl.styles import PatternFill, Font, Alignment
        except ImportError:
            QMessageBox.critical(
                self,
                "오류",
                "openpyxl 패키지가 설치되지 않았습니다.\npip install openpyxl 명령어로 설치해주세요.",
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Excel 내보내기",
            "",
            "Excel Files (*.xlsx)",
        )
        if not file_path:
            return

        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Capture Data"

            # 헤더 작성
            for col_idx, (field, header, group, editable, value_range) in enumerate(COLUMN_DEFINITIONS, start=1):
                cell = ws.cell(row=1, column=col_idx, value=header)

                # 배경색
                color = GROUP_COLORS.get(group, QColor(200, 200, 200))
                fill_color = f"{color.red():02X}{color.green():02X}{color.blue():02X}"
                cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')

            # 데이터 작성
            for row_idx, record in enumerate(self._model.get_all_records(), start=2):
                for col_idx, (field, header, group, editable, value_range) in enumerate(COLUMN_DEFINITIONS, start=1):
                    value = getattr(record, field, '')

                    # 타임스탬프 포맷팅
                    if field == 'timestamp':
                        minutes = int(value // 60)
                        seconds = value % 60
                        value = f"{minutes:02d}:{seconds:06.3f}"
                    elif field == 'capture_time' and isinstance(value, datetime):
                        value = value.strftime('%H:%M:%S')

                    cell = ws.cell(row=row_idx, column=col_idx, value=value)

                    # 수동 입력 컬럼 노랑 배경
                    if editable:
                        cell.fill = PatternFill(start_color="FFFF99", end_color="FFFF99", fill_type="solid")

                    # 위험 수준 셀 색상
                    if field in ('rula_risk', 'reba_risk', 'owas_risk'):
                        risk_color = RISK_COLORS.get(value, QColor(255, 255, 255))
                        fill_color = f"{risk_color.red():02X}{risk_color.green():02X}{risk_color.blue():02X}"
                        cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")

            # 컬럼 너비 자동 조정
            for col_idx in range(1, len(COLUMN_DEFINITIONS) + 1):
                ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = 12

            wb.save(file_path)
            QMessageBox.information(self, "완료", f"Excel 파일이 저장되었습니다:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 중 오류 발생:\n{str(e)}")

    def get_model(self) -> CaptureDataModel:
        """데이터 모델 반환"""
        return self._model

    def get_record_count(self) -> int:
        """레코드 수 반환"""
        return len(self._model)
