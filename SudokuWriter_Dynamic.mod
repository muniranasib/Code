
MODULE SudokuWriter

    CONST num gridSize := 4;

    CONST num largeCellSize := 50;
    CONST num smallCellSize := 37.5;

    CONST num largeBoardSize := 200;
    CONST num smallBoardSize := 150;

    ! Dynamic board geometry in the wobjA3 coordinate system (millimetres).
    ! Python/camera detection must update these values before drawing.
    PERS num boardOriginX := 0;
    PERS num boardOriginY := 0;
    PERS num boardCellSize := 50;
    PERS bool boardPositionValid := FALSE;

    CONST num penLift := 30;
    CONST num digitSize := 22;

    PERS tooldata toolPen :=
        [TRUE,[[0,0,75],[1,0,0,0]],
        [0.1,[0,0,75],[1,0,0,0],0,0,0]];

    PERS wobjdata wobjA3 :=
        [FALSE,TRUE,"",
        [[561.96,-199.06,0],[0.7071068,0,0,0.7071068]],
        [[0,0,0],[1,0,0,0]]];

    ! Temporary reference targets from the working motion test.
    PERS robtarget pStart :=
        [[5,-48.5,8],
         [0.029043357,0.000895114,0.999577752,-0.000026131],
         [0,1,-2,1],
         [9E9,9E9,9E9,9E9,9E9,9E9]];

    PERS robtarget pEnd :=
        [[205,-48.5,8],
         [0.029043357,0.000895114,0.999577752,-0.000026131],
         [0,1,-2,1],
         [9E9,9E9,9E9,9E9,9E9,9E9]];
         
    PERS num sudokuBoard{4,4} := [
        [4,2,0,0],
        [0,4,0,2],
        [2,0,4,0],
        [0,3,0,1]
    ];


    PROC SetBoardPosition(num originX, num originY, num cellSize)
        ! originX/originY is the TOP-LEFT corner of the Sudoku board
        ! in the same wobjA3 coordinate frame used by the drawing targets.
        IF cellSize <= 0 THEN
            TPWrite "Error: cell size must be positive";
            RETURN;
        ENDIF

        boardOriginX := originX;
        boardOriginY := originY;
        boardCellSize := cellSize;
        boardPositionValid := TRUE;

        TPWrite "Dynamic Sudoku board position updated";
        TPWrite "Origin X: "\Num:=boardOriginX;
        TPWrite "Origin Y: "\Num:=boardOriginY;
        TPWrite "Cell size: "\Num:=boardCellSize;
    ENDPROC


    PROC WriteDigit(
        num board,
        num row,
        num col,
        num digit)

        VAR num cellSize;
        VAR num cx;
        VAR num cy;

        IF NOT boardPositionValid THEN
            TPWrite "Error: call SetBoardPosition first";
            RETURN;
        ENDIF

        IF row < 1 OR row > gridSize OR
           col < 1 OR col > gridSize THEN
            TPWrite "Error: row or column out of range";
            RETURN;
        ENDIF

        IF digit < 1 OR digit > 4 THEN
            TPWrite "Error: digit must be 1-4";
            RETURN;
        ENDIF

        ! 'board' is retained in the procedure signature so existing calls
        ! to WriteBoard/SetCell remain compatible. Board selection is now dynamic.
        cellSize := boardCellSize;

        ! Board origin is its top-left corner.
        ! X increases from left to right; Y decreases from top to bottom.
        cx := boardOriginX + (col - 0.5) * cellSize;
        cy := boardOriginY - (row - 0.5) * cellSize;

        TPWrite "Row: "\Num:=row;
        TPWrite "Column: "\Num:=col;
        TPWrite "Digit: "\Num:=digit;
        TPWrite "Cell X: "\Num:=cx;
        TPWrite "Cell Y: "\Num:=cy;

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!           IF ELSE DIGIT LOGIC                !!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        
   
    IF digit = 1 THEN
        DrawDigit1 cx, cy, cellSize;
    ELSEIF digit = 2 THEN
        DrawDigit2 cx, cy, cellSize;
    ELSEIF digit = 3 THEN
        DrawDigit3 cx, cy, cellSize;
    ELSEIF digit = 4 THEN
        DrawDigit4 cx, cy, cellSize;
    ELSE
        TPWrite "Digit must be between 1 and 4";
    ENDIF

    ENDPROC
    
    
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!                     1                        !!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    
    
    
    PROC DrawDigit1(num cx, num cy, num cellSize)
        VAR num s;
        VAR robtarget pStart;
        VAR robtarget pJoin;
        VAR robtarget pEnd;
    
        s := cellSize * 0.20;
    
        ! Start at the upper-left end of the diagonal
        pStart := [[cx-s*0.65, cy-s*0.50, penLift],
                   [0.029043357,0.000895114,0.999577752,-0.000026131],
                   [0,1,-2,1],
                   [9E9,9E9,9E9,9E9,9E9,9E9]];
    
        ! Join point at the top of the vertical stroke
        pJoin := [[cx, cy+s*1.35, penLift],
                  [0.029043357,0.000895114,0.999577752,-0.000026131],
                  [0,1,-2,1],
                  [9E9,9E9,9E9,9E9,9E9,9E9]];
    
        ! Bottom of the vertical stroke
        pEnd := [[cx, cy-s*1.35, penLift],
                 [0.029043357,0.000895114,0.999577752,-0.000026131],
                 [0,1,-2,1],
                 [9E9,9E9,9E9,9E9,9E9,9E9]];
    
        ! Move above the start point
        MoveJ pStart, V30, fine, toolPen\WObj:=wobjA3;
    
        ! Lower pen
        MoveL Offs(pStart,0,0,-penLift),
              V30, fine, toolPen\WObj:=wobjA3;
    
        ! Draw diagonal towards the vertical stroke
        MoveL Offs(pJoin,0,0,-penLift),
              V30, fine, toolPen\WObj:=wobjA3;
    
        ! Draw vertical stroke
        MoveL Offs(pEnd,0,0,-penLift),
              V30, fine, toolPen\WObj:=wobjA3;
    
        ! Lift pen
        MoveL pEnd, V30, fine, toolPen\WObj:=wobjA3;
    ENDPROC


!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!                     2                        !!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   

    PROC DrawDigit2(num cx, num cy, num cellSize)
        VAR num s;
        VAR robtarget pStart;
        VAR robtarget pCurve1;
        VAR robtarget pCurve2;
        VAR robtarget pCurve3;
        VAR robtarget pMid;
        VAR robtarget pBottomLeft;
        VAR robtarget pBottomRight;

        s := cellSize * 0.20;

        ! Start at upper-left
        pStart := [[cx-s, cy+s*0.50, penLift],
                   [0.029043357,0.000895114,0.999577752,-0.000026131],
                   [0,1,-2,1],
                   [9E9,9E9,9E9,9E9,9E9,9E9]];

        ! Rounded top curve
        pCurve1 := [[cx-s*0.75, cy+s*0.90, penLift],
                    [0.029043357,0.000895114,0.999577752,-0.000026131],
                    [0,1,-2,1],
                    [9E9,9E9,9E9,9E9,9E9,9E9]];

        pCurve2 := [[cx, cy+s*1.35, penLift],
                    [0.029043357,0.000895114,0.999577752,-0.000026131],
                    [0,1,-2,1],
                    [9E9,9E9,9E9,9E9,9E9,9E9]];

        pCurve3 := [[cx+s*0.75, cy+s*0.90, penLift],
                    [0.029043357,0.000895114,0.999577752,-0.000026131],
                    [0,1,-2,1],
                    [9E9,9E9,9E9,9E9,9E9,9E9]];

        ! Diagonal down to the left
        pMid := [[cx+s*0.75, cy+s*0.15, penLift],
                 [0.029043357,0.000895114,0.999577752,-0.000026131],
                 [0,1,-2,1],
                 [9E9,9E9,9E9,9E9,9E9,9E9]];

        pBottomLeft := [[cx-s, cy-s*1.35, penLift],
                        [0.029043357,0.000895114,0.999577752,-0.000026131],
                        [0,1,-2,1],
                        [9E9,9E9,9E9,9E9,9E9,9E9]];

        pBottomRight := [[cx+s, cy-s*1.35, penLift],
                         [0.029043357,0.000895114,0.999577752,-0.000026131],
                         [0,1,-2,1],
                         [9E9,9E9,9E9,9E9,9E9,9E9]];

        ! Move above the start point
        MoveJ pStart, V30, fine, toolPen\WObj:=wobjA3;

        ! Lower pen
        MoveL Offs(pStart,0,0,-penLift),
              V30, fine, toolPen\WObj:=wobjA3;

        ! Rounded upper curve
        MoveL Offs(pCurve1,0,0,-penLift),
              V30, fine, toolPen\WObj:=wobjA3;
        MoveL Offs(pCurve2,0,0,-penLift),
              V30, fine, toolPen\WObj:=wobjA3;
        MoveL Offs(pCurve3,0,0,-penLift),
              V30, fine, toolPen\WObj:=wobjA3;

        ! Diagonal
        MoveL Offs(pMid,0,0,-penLift),
              V30, fine, toolPen\WObj:=wobjA3;

        ! Bottom stroke
        MoveL Offs(pBottomLeft,0,0,-penLift),
              V30, fine, toolPen\WObj:=wobjA3;
        MoveL Offs(pBottomRight,0,0,-penLift),
              V30, fine, toolPen\WObj:=wobjA3;

        ! Lift pen
        MoveL pBottomRight, V30, fine, toolPen\WObj:=wobjA3;
    ENDPROC


!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!                     3                        !!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    

    PROC DrawDigit3(num cx, num cy, num cellSize)
        VAR num s;
        VAR robtarget pStart;
        VAR robtarget pTopMid;
        VAR robtarget pTopRight;
        VAR robtarget pMiddle;
        VAR robtarget pLowerStart;
        VAR robtarget pLowerMid;
        VAR robtarget pBottom;

        s := cellSize * 0.20;

        ! Start at upper-left
        pStart := [[cx-s, cy+s*0.65, penLift],
                   [0.029043357,0.000895114,0.999577752,-0.000026131],
                   [0,1,-2,1],
                   [9E9,9E9,9E9,9E9,9E9,9E9]];

        ! Midpoint of upper curve
        pTopMid := [[cx+s*0.35, cy+s*0.95, penLift],
                    [0.029043357,0.000895114,0.999577752,-0.000026131],
                    [0,1,-2,1],
                    [9E9,9E9,9E9,9E9,9E9,9E9]];

        ! End of upper curve
        pTopRight := [[cx+s, cy+s*0.40, penLift],
                      [0.029043357,0.000895114,0.999577752,-0.000026131],
                      [0,1,-2,1],
                      [9E9,9E9,9E9,9E9,9E9,9E9]];

        ! Inward point at the middle of the digit
        pMiddle := [[cx-s*0.55, cy-s*0.05, penLift],
                    [0.029043357,0.000895114,0.999577752,-0.000026131],
                    [0,1,-2,1],
                    [9E9,9E9,9E9,9E9,9E9,9E9]];

        ! Start of lower curve
        pLowerStart := [[cx+s*0.35, cy-s*0.15, penLift],
                        [0.029043357,0.000895114,0.999577752,-0.000026131],
                        [0,1,-2,1],
                        [9E9,9E9,9E9,9E9,9E9,9E9]];

        ! Midpoint on the outer lower curve
        pLowerMid := [[cx+s*0.95, cy-s*0.80, penLift],
                      [0.029043357,0.000895114,0.999577752,-0.000026131],
                      [0,1,-2,1],
                      [9E9,9E9,9E9,9E9,9E9,9E9]];

        ! Bottom-left endpoint
        pBottom := [[cx-s*0.40, cy-s*1.25, penLift],
                    [0.029043357,0.000895114,0.999577752,-0.000026131],
                    [0,1,-2,1],
                    [9E9,9E9,9E9,9E9,9E9,9E9]];

        ! Move above the start
        MoveJ pStart, V30, fine, toolPen\WObj:=wobjA3;

        ! Lower pen
        MoveL Offs(pStart,0,0,-penLift),
              V30, fine, toolPen\WObj:=wobjA3;

        ! 1. Upper curve
        MoveC Offs(pTopMid,0,0,-penLift),
              Offs(pTopRight,0,0,-penLift),
              V30, fine, toolPen\WObj:=wobjA3;

        ! 2. Diagonal inward toward the middle
        MoveL Offs(pMiddle,0,0,-penLift),
              V30, fine, toolPen\WObj:=wobjA3;

        ! 3. Short straight transition
        MoveL Offs(pLowerStart,0,0,-penLift),
              V30, fine, toolPen\WObj:=wobjA3;

        ! 4. Rounded lower curve
        MoveC Offs(pLowerMid,0,0,-penLift),
              Offs(pBottom,0,0,-penLift),
              V30, fine, toolPen\WObj:=wobjA3;

        ! Lift pen
        MoveL pBottom, V30, fine, toolPen\WObj:=wobjA3;
    ENDPROC



    
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!                     4                        !!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    
    
    PROC DrawDigit4(num cx, num cy, num cellSize)
        VAR num s;
        VAR robtarget pStart;
        VAR robtarget pLeft;
        VAR robtarget pDiagonalTop;
        VAR robtarget pVerticalBottom;
    
        s := cellSize * 0.20;
    
        pStart := [[cx+s, cy-s*0.20, penLift],
            [0.029043357,0.000895114,0.999577752,-0.000026131],
            [0,1,-2,1],
            [9E9,9E9,9E9,9E9,9E9,9E9]];
    
        pLeft := [[cx-s, cy-s*0.20, penLift],
            [0.029043357,0.000895114,0.999577752,-0.000026131],
            [0,1,-2,1],
            [9E9,9E9,9E9,9E9,9E9,9E9]];
    
        pDiagonalTop := [[cx+s, cy+s, penLift],
            [0.029043357,0.000895114,0.999577752,-0.000026131],
            [0,1,-2,1],
            [9E9,9E9,9E9,9E9,9E9,9E9]];
    
        pVerticalBottom := [[cx+s, cy-s*1.35, penLift],
            [0.029043357,0.000895114,0.999577752,-0.000026131],
            [0,1,-2,1],
            [9E9,9E9,9E9,9E9,9E9,9E9]];
    
        MoveJ pStart,V30,fine,toolPen\WObj:=wobjA3;
        MoveL Offs(pStart,0,0,-penLift),V30,fine,toolPen\WObj:=wobjA3;
        MoveL Offs(pLeft,0,0,-penLift),V30,fine,toolPen\WObj:=wobjA3;
        MoveL Offs(pDiagonalTop,0,0,-penLift),V30,fine,toolPen\WObj:=wobjA3;
        MoveL Offs(pVerticalBottom,0,0,-penLift),V30,fine,toolPen\WObj:=wobjA3;
        MoveL pVerticalBottom,V30,fine,toolPen\WObj:=wobjA3;
    
    ENDPROC



    PROC WriteBoard(num board)
        VAR num row;
        VAR num col;
        VAR num digit;

        FOR row FROM 1 TO gridSize DO
            FOR col FROM 1 TO gridSize DO

                digit := sudokuBoard{row,col};

                IF digit <> 0 THEN
                    WriteDigit board,row,col,digit;
                ENDIF

            ENDFOR
        ENDFOR
    ENDPROC



    PROC SetCell(num board, num row, num col, num digit)
        IF board < 1 OR board > 2 THEN
            TPWrite "Error: board must be 1 or 2";
            RETURN;
        ENDIF

        IF row < 1 OR row > gridSize OR
           col < 1 OR col > gridSize THEN
            TPWrite "Error: row or column out of range";
            RETURN;
        ENDIF

        IF digit < 0 OR digit > 4 THEN
            TPWrite "Error: digit must be 0-4";
            RETURN;
        ENDIF

        sudokuBoard{row,col} := digit;

        TPWrite "Sudoku cell updated";
    ENDPROC



    
    PROC main()
        TPWrite "SudokuWriter ready. Set board position before drawing.";
        ! Example for a manual simulator test only:
        ! SetBoardPosition 5,101.5,50;
        ! WriteDigit 1,1,1,1;
    ENDPROC



ENDMODULE
