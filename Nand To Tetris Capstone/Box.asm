// Box.asm  --  K = 49
// While any key is pressed, draw a black box; when released, erase it.
//   start row   = K            = 49
//   height      = 20 rows
//   width       = 16*((K mod 4)+1) = 16*(1+1) = 32 pixels = 2 words
//   start addr  = SCREEN + 32*49 = 16384 + 1568 = 17952

(LOOP)
    @KBD
    D=M
    @BLACK
    D;JNE           // key pressed -> paint black
    @fill
    M=0             // no key -> paint white (erase)
    @PAINT
    0;JMP
(BLACK)
    @fill
    M=-1            // all 16 pixels set
(PAINT)
    @17952
    D=A
    @addr
    M=D             // addr = SCREEN + 32*49
    @20
    D=A
    @rows
    M=D             // rows = 20
(ROW)
    @fill
    D=M
    @addr
    A=M
    M=D             // word 0
    A=A+1
    M=D             // word 1  (2 words = 32 pixels)
    @32
    D=A
    @addr
    M=M+D           // next screen row
    @rows
    M=M-1
    D=M
    @ROW
    D;JGT
    @LOOP
    0;JMP
