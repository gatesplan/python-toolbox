import pytest
import portion as P
from state_cell.hysteresis import HysteresisCell, UnboundedValueError


class TestHysteresisCellInit:
    """HysteresisCell 초기화 테스트"""

    def test_init_with_string_intervals(self):
        # 문자열로 구간 정의
        cell = HysteresisCell('[-inf, 80]', '[20, inf)')

        assert len(cell.intervals) == 2
        assert cell.error_on_outside == False
        assert cell._state is None

    def test_init_with_interval_objects(self):
        # Interval 객체로 구간 정의
        cell = HysteresisCell(
            P.closed(0, 80),
            P.closed(20, 100)
        )

        assert len(cell.intervals) == 2
        assert cell._state is None

    def test_init_with_mixed_types(self):
        # 문자열과 Interval 객체 혼합
        cell = HysteresisCell(
            '[-inf, 80]',
            P.closed(20, 100)
        )

        assert len(cell.intervals) == 2

    def test_init_with_error_on_outside(self):
        # error_on_outside 파라미터
        cell = HysteresisCell(
            '[0, 100]', '[20, 120]',
            error_on_outside=True
        )

        assert cell.error_on_outside == True

    def test_init_requires_at_least_2_intervals(self):
        # 구간이 2개 미만이면 에러
        with pytest.raises(ValueError, match="at least 2 intervals"):
            HysteresisCell('[0, 100]')


class TestHysteresisCellInitialState:
    """HysteresisCell 초기 상태 결정 테스트"""

    def test_first_update_sets_initial_state(self):
        # 첫 update로 초기 상태 결정
        cell = HysteresisCell('[-inf, 80]', '[20, inf)')

        assert cell.get_state() is None

        result = cell.update(30)
        assert result == 0
        assert cell.get_state() == 0

    def test_first_update_multiple_intervals_chooses_first(self):
        # 여러 구간에 속할 때 첫 번째 구간 선택
        cell = HysteresisCell('[0, 100]', '[20, 120]')

        # 50은 두 구간 모두에 속함
        result = cell.update(50)
        assert result == 0  # 첫 번째 구간

    def test_first_update_outside_all_intervals_lenient(self):
        # 첫 update가 모든 구간 밖 (관대 모드)
        cell = HysteresisCell('[10, 50]', '[30, 80]', error_on_outside=False)

        result = cell.update(5)  # 모든 구간 밖
        assert result == 0  # 상태 0으로 시작

    def test_first_update_outside_all_intervals_strict(self):
        # 첫 update가 모든 구간 밖 (엄격 모드)
        cell = HysteresisCell(
            '[10, 50]', '[30, 80]',
            error_on_outside=True
        )

        with pytest.raises(UnboundedValueError):
            cell.update(5)


class TestHysteresisCellStateTransition:
    """HysteresisCell 상태 전환 테스트"""

    def test_state_maintained_within_interval(self):
        # 구간 내에서 상태 유지
        cell = HysteresisCell('[-inf, 80]', '[20, inf)')

        cell.update(30)  # 상태 0
        assert cell.update(40) == 0
        assert cell.update(50) == 0
        assert cell.update(70) == 0

    def test_state_transition_on_leaving_interval(self):
        # 구간을 벗어나면 상태 전환
        cell = HysteresisCell('[-inf, 80]', '[20, inf)')

        cell.update(30)  # 상태 0
        assert cell.get_state() == 0

        result = cell.update(85)  # 구간 0 벗어남, 구간 1 진입
        assert result == 1
        assert cell.get_state() == 1

    def test_hysteresis_effect_in_overlap_region(self):
        # 히스테리시스 효과: 겹침 영역에서 상태 유지
        cell = HysteresisCell('[-inf, 80]', '[20, inf)')

        # 상태 0에서 시작
        cell.update(30)
        assert cell.get_state() == 0

        # 겹침 영역 [20, 80]에서 상태 0 유지
        assert cell.update(40) == 0
        assert cell.update(60) == 0
        assert cell.update(75) == 0

        # 구간 0 벗어남 → 상태 1
        assert cell.update(85) == 1

        # 겹침 영역 [20, 80]에서 상태 1 유지!
        assert cell.update(70) == 1
        assert cell.update(50) == 1
        assert cell.update(25) == 1

        # 구간 1 벗어남 → 상태 0
        assert cell.update(15) == 0

    def test_bidirectional_transitions(self):
        # 양방향 전환
        cell = HysteresisCell('[-inf, 80]', '[20, inf)')

        cell.update(30)  # 0
        assert cell.update(85) == 1  # 0 -> 1
        assert cell.update(15) == 0  # 1 -> 0
        assert cell.update(90) == 1  # 0 -> 1
        assert cell.update(10) == 0  # 1 -> 0


class TestHysteresisCellMultipleStates:
    """HysteresisCell 3개 이상 상태 테스트"""

    def test_three_state_hysteresis(self):
        # 3-상태 히스테리시스
        cell = HysteresisCell(
            '[-inf, 20]',   # 상태 0: COLD
            '[15, 30]',     # 상태 1: NORMAL
            '[25, inf)'     # 상태 2: HOT
        )

        # COLD 시작
        assert cell.update(10) == 0

        # 겹침 영역 15-20에서 COLD 유지 (현재 상태 우선)
        assert cell.update(18) == 0

        # COLD 구간 벗어남, NORMAL 진입
        assert cell.update(22) == 1

        # 겹침 영역 25-30에서 NORMAL 유지 (현재 상태 우선)
        assert cell.update(28) == 1

        # NORMAL 구간 벗어남, HOT 진입
        assert cell.update(35) == 2

        # HOT 유지 (겹침 영역에서도)
        assert cell.update(27) == 2
        assert cell.update(26) == 2

        # COLD로 직접 전환
        assert cell.update(12) == 0


class TestHysteresisCellOutsideBehavior:
    """HysteresisCell 구간 밖 값 처리 테스트"""

    def test_outside_value_maintains_state_lenient(self):
        # 관대 모드: 구간 밖 값이면 상태 유지
        cell = HysteresisCell('[10, 50]', '[30, 80]', error_on_outside=False)

        cell.update(20)  # 상태 0
        assert cell.get_state() == 0

        # 구간 밖 값
        result = cell.update(5)
        assert result == 0  # 상태 유지

        result = cell.update(90)
        assert result == 0  # 여전히 상태 유지

    def test_outside_value_raises_error_strict(self):
        # 엄격 모드: 구간 밖 값이면 에러
        cell = HysteresisCell('[10, 50]', '[30, 80]', error_on_outside=True)

        cell.update(20)  # 상태 0

        with pytest.raises(UnboundedValueError, match="outside all defined intervals"):
            cell.update(5)

        with pytest.raises(UnboundedValueError):
            cell.update(90)


class TestHysteresisCellReset:
    """HysteresisCell reset 테스트"""

    def test_reset_clears_state(self):
        # reset 시 상태 None
        cell = HysteresisCell('[-inf, 80]', '[20, inf)')

        cell.update(30)
        assert cell.get_state() == 0

        cell.reset()
        assert cell.get_state() is None

    def test_reset_allows_reinitialization(self):
        # reset 후 재초기화 가능
        cell = HysteresisCell('[0, 100]', '[50, 150]')

        cell.update(30)
        assert cell.get_state() == 0

        cell.reset()

        # 다른 구간으로 재초기화
        result = cell.update(120)
        assert result == 1


class TestHysteresisCellEdgeCases:
    """HysteresisCell 경계 케이스 테스트"""

    def test_exact_boundary_values(self):
        # 정확히 경계값
        cell = HysteresisCell('[0, 80]', '[20, 100]')

        cell.update(50)
        assert cell.get_state() == 0

        # 정확히 80 (구간 0의 상한)
        assert cell.update(80) == 0

        # 80을 벗어남
        assert cell.update(85) == 1

        # 정확히 20 (구간 1의 하한)
        assert cell.update(20) == 1

        # 20 미만
        assert cell.update(15) == 0

    def test_open_vs_closed_intervals(self):
        # 개구간 vs 폐구간
        cell = HysteresisCell('(0, 80)', '[20, 100]')

        # 0은 개구간 (0, 80)에 포함 안 됨, [20, 100]에도 안 됨
        # 첫 update시 어느 구간에도 속하지 않으면 상태 0으로 시작
        result = cell.update(0)
        assert result == 0

        # 50은 (0, 80)과 [20, 100] 모두에 속함
        # 현재 상태 0이고, 50이 구간 0에 속하므로 상태 유지
        result = cell.update(50)
        assert result == 0

        # 90은 구간 0을 벗어나고, 구간 1에만 속함
        result = cell.update(90)
        assert result == 1

    def test_infinite_intervals(self):
        # 무한 구간
        cell = HysteresisCell('[-inf, 50]', '[30, inf)')

        cell.update(-1000)
        assert cell.get_state() == 0

        cell.update(1000)
        assert cell.get_state() == 1


class TestHysteresisCellWithStateManager:
    """HysteresisCell과 StateManager 통합 테스트"""

    def test_integration_with_state_manager(self):
        from state_cell import StateManager

        manager = StateManager(
            cell=HysteresisCell('[-inf, 80]', '[20, inf)'),
            states=['LOW', 'HIGH'],
            initial='LOW'
        )

        # 상태 변경 추적
        changes = []
        manager.add_listener(lambda old, new: changes.append((old, new)))

        # 초기 상태
        assert manager.get_state() == 'LOW'

        # 상태 유지
        result = manager.update(50)
        assert result == 'LOW'
        assert len(changes) == 0

        # 상태 전환
        result = manager.update(85)
        assert result == 'HIGH'
        assert len(changes) == 1
        assert changes[0] == ('LOW', 'HIGH')

        # 히스테리시스 영역에서 상태 유지
        result = manager.update(70)
        assert result == 'HIGH'
        assert len(changes) == 1

        # 다시 전환
        result = manager.update(15)
        assert result == 'LOW'
        assert len(changes) == 2
        assert changes[1] == ('HIGH', 'LOW')
