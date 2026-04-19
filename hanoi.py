from __future__ import annotations

import time
from dataclasses import dataclass


ANSI_RESET = "\033[0m"
ANSI_DISK_COLORS = (
    "\033[31m",
    "\033[32m",
    "\033[33m",
    "\033[34m",
    "\033[35m",
    "\033[36m",
)


@dataclass
class SolverResult:
    moves: list[tuple[int, int]]
    solved: bool
    reason: str


class HanoiGame:
    def __init__(self, disk_count: int) -> None:
        if disk_count < 1:
            raise ValueError("disk_count must be at least 1")

        self.disk_count = disk_count
        self._pegs: list[list[int]] = [list(range(disk_count, 0, -1)), [], []]
        self._labels = ("A", "B", "C")

    @property
    def pegs(self) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
        return tuple(tuple(peg) for peg in self._pegs)

    def can_move(self, from_peg: int, to_peg: int) -> bool:
        self._validate_peg_index(from_peg)
        self._validate_peg_index(to_peg)

        if from_peg == to_peg:
            return False

        source = self._pegs[from_peg]
        target = self._pegs[to_peg]

        if not source:
            return False

        if not target:
            return True

        return source[-1] < target[-1]

    def move_disk(self, from_peg: int, to_peg: int) -> None:
        if not self.can_move(from_peg, to_peg):
            raise ValueError(
                f"cannot move disk from {self._labels[from_peg]} to {self._labels[to_peg]}"
            )

        disk = self._pegs[from_peg].pop()
        self._pegs[to_peg].append(disk)

    def solve_recursively(self, print_steps: bool = False) -> list[tuple[int, int]]:
        moves: list[tuple[int, int]] = []

        if print_steps:
            print("Initial state:")
            self.print_board()

        self._solve_recursive(
            disk_count=self.disk_count,
            source=0,
            target=2,
            auxiliary=1,
            moves=moves,
            print_steps=print_steps,
        )
        return moves

    def solve_with_largest_movable_top(
        self, print_steps: bool = False
    ) -> SolverResult:
        moves: list[tuple[int, int]] = []
        seen_states = {self.pegs}
        last_moved_disk: int | None = None

        if print_steps:
            print("Initial state:")
            self.print_board()

        max_moves = 100

        while not self._has_recreated_initial_stack_elsewhere():
            if len(moves) >= max_moves:
                return SolverResult(
                    moves=moves,
                    solved=False,
                    reason=f"exceeded move limit ({max_moves})",
                )

            move = self._choose_largest_movable_top_move(
                excluded_disk=last_moved_disk
            )
            if move is None:
                return SolverResult(
                    moves=moves,
                    solved=False,
                    reason="no legal move available after excluding the last moved disk",
                )

            source, target = move
            last_moved_disk = self._pegs[source][-1]
            self.move_disk(source, target)
            moves.append(move)

            if print_steps:
                move_number = len(moves)
                print(
                    f"Move {move_number}: {self._labels[source]} -> {self._labels[target]}"
                )
                self.print_board()

            time.sleep(1)

            state = self.pegs
            if state in seen_states:
                if print_steps:
                    print(f"(cycle detected at move {len(moves)})")
            else:
                seen_states.add(state)

        return SolverResult(
            moves=moves,
            solved=True,
            reason="initial tower reproduced on another peg",
        )

    def is_solved(self) -> bool:
        return len(self._pegs[2]) == self.disk_count

    def render(self) -> str:
        lines: list[str] = []
        max_disk_width = self.disk_count * 2 - 1
        peg_spacing = 4

        for level in range(self.disk_count - 1, -1, -1):
            row_parts: list[str] = []
            for peg in self._pegs:
                disk = peg[level] if level < len(peg) else 0
                row_parts.append(self._render_disk(disk, max_disk_width))
            lines.append((" " * peg_spacing).join(row_parts))

        base_width = max_disk_width * len(self._pegs) + peg_spacing * (len(self._pegs) - 1)
        lines.append("-" * base_width)
        lines.append(self._render_labels(max_disk_width, peg_spacing))

        return "\n".join(lines)

    def print_board(self) -> None:
        print(self.render())
        print()

    def _solve_recursive(
        self,
        disk_count: int,
        source: int,
        target: int,
        auxiliary: int,
        moves: list[tuple[int, int]],
        print_steps: bool,
    ) -> None:
        if disk_count == 0:
            return

        self._solve_recursive(
            disk_count=disk_count - 1,
            source=source,
            target=auxiliary,
            auxiliary=target,
            moves=moves,
            print_steps=print_steps,
        )

        self.move_disk(source, target)
        moves.append((source, target))

        if print_steps:
            move_number = len(moves)
            print(
                f"Move {move_number}: {self._labels[source]} -> {self._labels[target]}"
            )
            self.print_board()

        self._solve_recursive(
            disk_count=disk_count - 1,
            source=auxiliary,
            target=target,
            auxiliary=source,
            moves=moves,
            print_steps=print_steps,
        )

    def _choose_largest_movable_top_move(
        self, excluded_disk: int | None = None
    ) -> tuple[int, int] | None:
        candidate_sources: list[int] = []

        for peg_index, peg in enumerate(self._pegs):
            if not peg:
                continue

            if excluded_disk is not None and peg[-1] == excluded_disk:
                continue

            legal_targets = self._legal_targets_for(peg_index)
            if legal_targets:
                candidate_sources.append(peg_index)

        if not candidate_sources:
            return None

        source = max(candidate_sources, key=lambda peg_index: self._pegs[peg_index][-1])
        legal_targets = self._legal_targets_for(source)
        target = min(
            legal_targets,
            key=lambda peg_index: (self._target_top_value_for_strategy(peg_index), peg_index),
        )
        return source, target

    def _legal_targets_for(self, source: int) -> list[int]:
        return [target for target in range(3) if self.can_move(source, target)]

    def _target_top_value_for_strategy(self, peg_index: int) -> float:
        peg = self._pegs[peg_index]
        if not peg:
            return 0.0
        return float(peg[-1])

    def _has_recreated_initial_stack_elsewhere(self) -> bool:
        initial_stack = tuple(range(self.disk_count, 0, -1))
        return any(tuple(peg) == initial_stack for peg in self._pegs[1:])

    def _render_disk(self, disk: int, max_disk_width: int) -> str:
        if disk == 0:
            return "|".center(max_disk_width)

        body = "=" * (disk * 2 - 1)
        centered_body = body.center(max_disk_width)
        color = ANSI_DISK_COLORS[(disk - 1) % len(ANSI_DISK_COLORS)]
        return f"{color}{centered_body}{ANSI_RESET}"

    def _render_labels(self, max_disk_width: int, peg_spacing: int) -> str:
        return (" " * peg_spacing).join(
            label.center(max_disk_width) for label in self._labels
        )

    def _validate_peg_index(self, peg_index: int) -> None:
        if peg_index not in (0, 1, 2):
            raise IndexError("peg index must be 0, 1, or 2")


def main() -> None:
    game = HanoiGame(disk_count=5)
    result = game.solve_with_largest_movable_top(print_steps=True)

    if result.solved:
        print(f"Solved in {len(result.moves)} moves.")
    else:
        print(f"Stopped after {len(result.moves)} moves: {result.reason}")


if __name__ == "__main__":
    main()