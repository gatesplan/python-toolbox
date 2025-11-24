import pytest
from state_cell.threshold import ThresholdCell


class TestThresholdCellInit:
    """ThresholdCell 초기화 테스트"""

    def test_init_with_single_threshold(self):
        # 단일 threshold
        cell = ThresholdCell(50)
        assert cell.thresholds == [50]
        assert cell._state is None

    def test_init_with_multiple_thresholds(self):
        # 다중 threshold
        cell = ThresholdCell(20, 50, 80)
        assert cell.thresholds == [20, 50, 80]

    def test_init_auto_sorts_thresholds(self):
        # 자동 정렬
        cell = ThresholdCell(80, 20, 50)
        assert cell.thresholds == [20, 50, 80]

    def test_init_requires_at_least_one_threshold(self):
        # 최소 1개 필요
        with pytest.raises(ValueError, match="at least 1 threshold"):
            ThresholdCell()

    def test_init_rejects_duplicate_thresholds(self):
        # 중복 threshold 에러
        with pytest.raises(ValueError, match="Duplicate thresholds"):
            ThresholdCell(50, 80, 50)


class TestThresholdCellInitialState:
    """ThresholdCell 초기 상태 결정 테스트"""

    def test_first_update_below_threshold(self):
        # threshold 아래
        cell = ThresholdCell(50)
        assert cell.update(30) == 0

    def test_first_update_above_threshold(self):
        # threshold 위
        cell = ThresholdCell(50)
        assert cell.update(70) == 1

    def test_first_update_on_threshold(self):
        # threshold와 같을 때 (경계값 = 이전 유지, 하지만 첫 호출이므로 계산)
        cell = ThresholdCell(50)
        # 50은 threshold를 넘지 않음 → 상태 0
        assert cell.update(50) == 0

    def test_first_update_multiple_thresholds(self):
        # 다중 threshold
        cell = ThresholdCell(20, 50, 80)

        cell1 = ThresholdCell(20, 50, 80)
        assert cell1.update(10) == 0

        cell2 = ThresholdCell(20, 50, 80)
        assert cell2.update(30) == 1

        cell3 = ThresholdCell(20, 50, 80)
        assert cell3.update(60) == 2

        cell4 = ThresholdCell(20, 50, 80)
        assert cell4.update(90) == 3


class TestThresholdCellBoundaryBehavior:
    """ThresholdCell 경계값 처리 테스트"""

    def test_boundary_value_maintains_state(self):
        # 경계값 = 이전 상태 유지
        cell = ThresholdCell(50)

        cell.update(40)  # 상태 0
        assert cell.update(50) == 0  # 경계값, 0 유지

        cell.update(60)  # 상태 1
        assert cell.update(50) == 1  # 경계값, 1 유지

    def test_boundary_cross_detailed(self):
        # 사용자 예시: 40->50->51->50->49
        cell = ThresholdCell(50)

        assert cell.update(40) == 0  # 초기
        assert cell.update(50) == 0  # 경계값, 0 유지
        assert cell.update(51) == 1  # 50 경계 넘음! cross over
        assert cell.update(50) == 1  # 경계값, 1 유지
        assert cell.update(49) == 0  # 50 경계 넘음! sink under


class TestThresholdCellStateTransition:
    """ThresholdCell 상태 전환 테스트"""

    def test_state_maintained_within_range(self):
        # 범위 내에서 상태 유지
        cell = ThresholdCell(50)

        cell.update(30)
        assert cell.update(35) == 0
        assert cell.update(40) == 0
        assert cell.update(45) == 0

    def test_state_transition_on_crossing(self):
        # 경계 넘을 때만 전환
        cell = ThresholdCell(50)

        assert cell.update(30) == 0
        assert cell.update(60) == 1  # 50 넘음
        assert cell.update(40) == 0  # 50 밑으로

    def test_bidirectional_transitions(self):
        # 양방향 전환
        cell = ThresholdCell(50)

        assert cell.update(30) == 0
        assert cell.update(60) == 1  # 0 -> 1
        assert cell.update(40) == 0  # 1 -> 0
        assert cell.update(70) == 1  # 0 -> 1
        assert cell.update(30) == 0  # 1 -> 0


class TestThresholdCellMultipleStates:
    """ThresholdCell 다중 상태 테스트"""

    def test_three_state_threshold(self):
        # 3-상태 (2개 threshold)
        cell = ThresholdCell(50, 80)

        # 상태 0: ~ 50
        assert cell.update(30) == 0
        assert cell.update(40) == 0

        # 상태 1: 50 ~ 80
        assert cell.update(60) == 1
        assert cell.update(70) == 1

        # 상태 2: 80 ~
        assert cell.update(90) == 2
        assert cell.update(100) == 2

    def test_four_state_threshold(self):
        # 4-상태 (3개 threshold)
        cell = ThresholdCell(20, 50, 80)

        assert cell.update(10) == 0
        assert cell.update(30) == 1
        assert cell.update(60) == 2
        assert cell.update(90) == 3

    def test_multi_state_transitions(self):
        # 다중 상태 전환
        cell = ThresholdCell(20, 50, 80)

        assert cell.update(10) == 0
        assert cell.update(30) == 1  # 20 넘음
        assert cell.update(60) == 2  # 50 넘음
        assert cell.update(40) == 1  # 50 밑으로
        assert cell.update(15) == 0  # 20 밑으로
        assert cell.update(90) == 3  # 20, 50, 80 모두 넘음

    def test_multi_boundary_values(self):
        # 다중 경계값
        cell = ThresholdCell(20, 50, 80)

        cell.update(10)  # 상태 0
        assert cell.update(20) == 0  # 경계값, 0 유지

        cell.update(30)  # 상태 1
        assert cell.update(20) == 1  # 경계값, 1 유지
        assert cell.update(50) == 1  # 경계값, 1 유지

        cell.update(60)  # 상태 2
        assert cell.update(50) == 2  # 경계값, 2 유지
        assert cell.update(80) == 2  # 경계값, 2 유지

        cell.update(90)  # 상태 3
        assert cell.update(80) == 3  # 경계값, 3 유지


class TestThresholdCellReset:
    """ThresholdCell reset 테스트"""

    def test_reset_clears_state(self):
        cell = ThresholdCell(50)

        cell.update(60)
        assert cell.get_state() == 1

        cell.reset()
        assert cell.get_state() is None

    def test_reset_allows_reinitialization(self):
        cell = ThresholdCell(50)

        cell.update(60)
        assert cell.get_state() == 1

        cell.reset()

        # 다른 값으로 재초기화
        assert cell.update(30) == 0


class TestThresholdCellEdgeCases:
    """ThresholdCell 경계 케이스 테스트"""

    def test_negative_thresholds(self):
        # 음수 threshold
        cell = ThresholdCell(-50, 0, 50)

        assert cell.update(-100) == 0
        assert cell.update(-25) == 1
        assert cell.update(25) == 2
        assert cell.update(75) == 3

    def test_floating_point_thresholds(self):
        # 실수 threshold
        cell = ThresholdCell(10.5, 20.7, 30.9)

        assert cell.update(5.0) == 0
        assert cell.update(15.0) == 1
        assert cell.update(25.0) == 2
        assert cell.update(35.0) == 3

    def test_very_large_values(self):
        # 매우 큰 값
        cell = ThresholdCell(50)

        assert cell.update(float('inf')) == 1
        assert cell.update(float('-inf')) == 0


class TestThresholdCellWithStateManager:
    """ThresholdCell과 StateManager 통합 테스트"""

    def test_integration_with_state_manager(self):
        from state_cell import StateManager

        manager = StateManager(
            cell=ThresholdCell(50),
            states=['BELOW', 'ABOVE'],
            initial='BELOW'
        )

        # 상태 변경 추적
        changes = []
        manager.add_listener(lambda old, new: changes.append((old, new)))

        # 초기 상태
        assert manager.get_state() == 'BELOW'

        # 상태 유지
        result = manager.update(40)
        assert result == 'BELOW'
        assert len(changes) == 0

        # 상태 전환
        result = manager.update(60)
        assert result == 'ABOVE'
        assert len(changes) == 1
        assert changes[0] == ('BELOW', 'ABOVE')

        # 경계값에서 유지
        result = manager.update(50)
        assert result == 'ABOVE'
        assert len(changes) == 1  # 변경 없음

        # 다시 전환
        result = manager.update(40)
        assert result == 'BELOW'
        assert len(changes) == 2
        assert changes[1] == ('ABOVE', 'BELOW')

    def test_multi_state_with_state_manager(self):
        from state_cell import StateManager

        manager = StateManager(
            cell=ThresholdCell(20, 50, 80),
            states=['COLD', 'COOL', 'WARM', 'HOT'],
            initial='COLD'
        )

        changes = []
        manager.add_listener(lambda old, new: changes.append((old, new)))

        assert manager.update(10) == 'COLD'
        assert manager.update(30) == 'COOL'
        assert len(changes) == 1
        assert changes[0] == ('COLD', 'COOL')

        assert manager.update(60) == 'WARM'
        assert manager.update(90) == 'HOT'
        assert len(changes) == 3
