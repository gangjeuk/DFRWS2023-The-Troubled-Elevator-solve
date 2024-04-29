#pragma once

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/select.h>

#include <signal.h>
#include <sys/time.h>

#include <termios.h>
#include <time.h>
#include <unistd.h>

extern int carry_flag;

// r14 register
// Tmp
extern unsigned long long r14;
extern unsigned long long idx;
extern int stack[100];

// Timer
#define ONE_SEC 1000
extern unsigned long long start_time;
#define SET_TIMER 0x0001
#define DN0 0x0002
#define DN1 0x0004
struct TON{
  time_t start;
  time_t sec_preset;
  int timer_started;
};

void handle_timer(struct TON *t){
  if(t->timer_started == 1){
    time_t time_now;
    time(&time_now);
    time_t time_passed = time_now - t->start;
    // clock finished
    if(time_passed > t->sec_preset){
      printf("Timer finished: %lus\n", t->sec_preset);
      t->timer_started = 0;
      carry_flag = 1;
    }
    // else TST DN should be False
    else{
      carry_flag = 0;
    }
  }
  else if(t->timer_started == 0 && carry_flag == 1){
    printf("Timer started: %lus\n", t->sec_preset);
    t->timer_started = 1;
    time(&t->start);
    // else TST DN should be False
      carry_flag = 0;
  }
}


// r11 register
// Rotation and Status
extern unsigned long long r11;

// r13 register
// Connected to Output
extern unsigned long long r13;
#define UP 0x0001
#define DOWN 0x0002
#define FD_C 0x0004
#define DOOR_OPEN 0x0008
#define FD_AGD 0x0010
#define FD_E 0x0020
#define DOOR_CLOSE 0x0040

// r12 register
// Connected to Input
extern unsigned long long r12;
#define LIMIT_SWITCH_FLOOR_1 0x0001
#define LIMIT_SWITCH_FLOOR_2 0x0002
#define LIMIT_SWITCH_FLOOR_3 0x0004

#define DOOR_LIMIT_CLOSE 0x0008

#define NO_EXTERNAL_CALLING_BUTTON_4 0x0010
#define EXTERNAL_CALLING_BUTTON_1 0x0020
#define EXTERNAL_CALLING_BUTTON_2 0x0040
#define EXTERNAL_CALLING_BUTTON_3 0x0080

#define DOOR_LIMIT_OPEN 0x0100

// r7 register
// Address of the block of data object
extern unsigned long long r7;

#define WAS_AT_FLOOR_4 0x0001
#define WAS_AT_FLOOR_1 0x0002
#define WAS_AT_FLOOR_2 0x0004
#define WAS_AT_FLOOR_3 0x0008

#define FLOOR_1_CALL 0x0010
#define FLOOR_2_CALL 0x0020
#define FLOOR_3_CALL 0x0040

#define AT_FLOOR_1 0x0080
#define AT_FLOOR_2 0x0100
#define AT_FLOOR_3 0x0200

#define FLOOR_4_CALL (1UL << 10)
#define AT_FLOOR_4 (1UL << 11)

#define DOOR_CNT (1UL << 12)

#define M20 (1UL << 20)
#define M21 (1UL << 21)

#define FLOOR_1_LATCH (1UL << 30)
#define FLOOR_2_LATCH (1UL << 31)
#define FLOOR_3_LATCH (1UL << 32)

#define ATTACK (1UL << 35)

#define SAME_FLOOR_CALL (1UL << 60)

#define __BNC(addr, expression)                                                \
  do {                                                                         \
    if (expression) {                                                          \
      goto addr;                                                               \
    }                                                                          \
  } while (0)
#define BNC(addr) __BNC(addr, carry_flag == 0)
#define BC(addr) __BNC(addr, carry_flag == 1)
#define SET(reg, flag) (set(&reg, flag, #reg))
#define CLR(reg, flag) (clr(&reg, flag, #reg))
#define BMC(reg, flag) (bmc(&reg, flag, #reg))
#define TST(reg, flag) (tst(reg, flag, #reg))
#define MOV(src_val, dest_reg) (mov(src_val, &dest_reg, #dest_reg))
#define NOT(reg) (reg = ~reg)
#define RORC(reg) (rorc(&reg))
#define ROLC(reg) (rolc(&reg))
#define STR(arg) #arg

#define COMMAND(arg, reg)                                                      \
  { arg, #arg, #reg }

struct command {
  unsigned long long flag;
  char *name;
  char *reg_name;
};

const struct command command[] = {
    COMMAND(SET_TIMER, timer),
    COMMAND(DN0, timer),
    COMMAND(DN1, timer),
    COMMAND(WAS_AT_FLOOR_1, r7),
    COMMAND(WAS_AT_FLOOR_2, r7),
    COMMAND(WAS_AT_FLOOR_3, r7),
    COMMAND(FLOOR_1_CALL, r7),
    COMMAND(FLOOR_2_CALL, r7),
    COMMAND(FLOOR_3_CALL, r7),
    COMMAND(FLOOR_4_CALL, r7),
    COMMAND(AT_FLOOR_1, r7),
    COMMAND(AT_FLOOR_2, r7),
    COMMAND(AT_FLOOR_3, r7),
    COMMAND(AT_FLOOR_4, r7),
    COMMAND(DOOR_CNT, r7),
    COMMAND(M20, r7),
    COMMAND(M21, r7),
    COMMAND(FLOOR_1_LATCH, r7),
    COMMAND(FLOOR_2_LATCH, r7),
    COMMAND(FLOOR_3_LATCH, r7),
    COMMAND(ATTACK, r7),
    COMMAND(SAME_FLOOR_CALL, r7),
    COMMAND(UP, r13),
    COMMAND(DOWN, r13),
    COMMAND(FD_C, r13),
    COMMAND(DOOR_OPEN, r13),
    COMMAND(FD_AGD, r13),
    COMMAND(FD_E, r13),
    COMMAND(DOOR_CLOSE, r13),
    COMMAND(LIMIT_SWITCH_FLOOR_1, r12),
    COMMAND(LIMIT_SWITCH_FLOOR_2, r12),
    COMMAND(LIMIT_SWITCH_FLOOR_3, r12),
    COMMAND(DOOR_LIMIT_CLOSE, r12),
    COMMAND(DOOR_LIMIT_OPEN, r12),
    COMMAND(NO_EXTERNAL_CALLING_BUTTON_4, r12),
    COMMAND(EXTERNAL_CALLING_BUTTON_1, r12),
    COMMAND(EXTERNAL_CALLING_BUTTON_2, r12),
    COMMAND(EXTERNAL_CALLING_BUTTON_3, r12),
};

int shift_cnt(unsigned long long flag) {
  int i = 0;
  while (flag >> 1 != 0) {
    flag >>= 1;
    i += 1;
  }
  return i;
}

void push(int val) { stack[idx++] = val; }

int pop() {
  if (idx == 0) {
    printf("error\n");
    exit(1);
  }
  int ret = stack[--idx];
  return ret;
}
#define POP(reg) (reg = pop())
#define PUSH(val) (push(val))

char *pick_name(unsigned long long flag, char *reg_name) {
  for (int i = 0; i < sizeof(command) / sizeof(struct command); i++) {
    if (command[i].flag == flag && strcmp(reg_name, command[i].reg_name) == 0)
      return command[i].name;
  }
  return NULL;
}
char *pick_reg_name(unsigned long long flag) {
  for (int i = 0; i < sizeof(command) / sizeof(struct command); i++) {
    if (command[i].flag == flag)
      return command[i].reg_name;
  }

  return NULL;
}

void debug_print(char *func_name, unsigned long long *reg,
                 unsigned long long flag, char *reg_name) {
  //printf("Register %s %s %s\n", reg_name, func_name, pick_name(flag, reg_name));
}

void rorc(unsigned long long *reg) {
  unsigned int tmp = carry_flag;
  // printf("RORC\n");
  // printf("Reg: %llx\n", *reg);
  carry_flag = (*reg) & 0x1;
  *reg >>= 1UL;
  if (tmp == 0UL) {
    *reg &= 0x7FFFFFFFUL;
  } else {
    *reg |= 0x80000000UL;
  }
  // printf("Carry flag: %x -> %x\n", tmp, carry_flag);
  // printf("Reg: %llx\n", *reg);
  return;
}
void rolc(unsigned long long *reg) {
  unsigned int tmp = carry_flag;
  // printf("ROLC\n");
  // printf("Reg: %llx\n", *reg);
  *reg <<= 1UL;
  carry_flag = (*reg) & 0x100000000UL;
  if (tmp == 0UL) {
    *reg &= 0x00000000FFFFFFFEUL;
  } else {
    *reg |= 0x00000001UL;
  }
  // printf("Carry flag: %x -> %x\n", tmp, carry_flag);
  // printf("Reg: %llx\n", *reg);
  return;
}

void mov(unsigned long long src, unsigned long long *reg, char *reg_name) {
  // printf("Mov\n");
  // printf("reg: 0x%llx\n", *reg);
  // printf("Mov reg:%s - 0x%llx\n", reg_name, src);
  *reg = src;
  // printf("reg: 0x%llx\n", *reg);
  return;
}
void clr(unsigned long long *reg, unsigned long long flag, char *reg_name) {
  flag = 1UL << flag;
  *reg = *reg & (~flag);
  if (pick_name(flag, reg_name) != NULL)
    debug_print("CLR", reg, flag, reg_name);
  return;
}
void set(unsigned long long *reg, unsigned long long flag, char *reg_name) {
  flag = 1UL << flag;
  *reg = *reg | flag;
  if (pick_name(flag, reg_name) != NULL)
    debug_print("SET", reg, flag, reg_name);
  return;
}
void bmc(unsigned long long *reg, unsigned long long flag, char *reg_name) {
  // printf("BMC %s \t", reg_name);
  if (carry_flag == 1UL) {
    set(reg, flag, reg_name);
  } else {
    clr(reg, flag, reg_name);
  }
}

void tst(unsigned long long reg, unsigned long long flag, char *reg_name) {
  flag = 1UL << flag;
  // printf("Register %s Tested %s\n", reg_name, pick_name(flag, reg_name));
  if (reg & flag)
    carry_flag = 1UL;
  else
    carry_flag = 0UL;

  return;
}



void call_r14_4() {
  BNC(x8);
  TST(r11, 31UL);
x8:
  return;
}
void call_r14_a() {
  BC(x8);
  TST(r11, 31UL);
x8:
  return;
}

#define JSR_r14()                                                              \
  do {                                                                         \
    if (r14 == 4) {                                                            \
      call_r14_4();                                                            \
    } else if (r14 == 0xA) {                                                   \
      call_r14_a();                                                            \
    } else {                                                                   \
      printf("JSR_r14 to null\n");                                             \
    }                                                                          \
  } while (0)


void init_state();
void what_floor();
void first_called();
void second_called();
void third_called();
void floor_display();
void elevator_door();

extern unsigned int elevator_floor;
extern unsigned int door_level;

int simulation(unsigned int input) {
  if ((r13 & DOOR_OPEN) && door_level < 10) {
    door_level += 5;
  } else if ((r13 & DOOR_CLOSE) && door_level > 0) {
    door_level -= 5;
  }

  // 1s for each loop
  // About 10s needed for moving one floor.(e.g 1F -> 2F, 3F -> 2F)
  if ((r13 & UP) && elevator_floor < 30) {
    elevator_floor += 1;
  } else if ((r13 & DOWN) && elevator_floor > 10) {
    elevator_floor -= 1;
  }

  // LIMIT_SWITCH_FLOOR_N: floor sensor
  // ex) LIMIT_SWITCH_FLOOR_2 means elevator is on second floor
  if (elevator_floor == 30) {
    CLR(r12, shift_cnt(LIMIT_SWITCH_FLOOR_1));
    CLR(r12, shift_cnt(LIMIT_SWITCH_FLOOR_2));
    CLR(r12, shift_cnt(LIMIT_SWITCH_FLOOR_3));
    SET(r12, shift_cnt(LIMIT_SWITCH_FLOOR_3));
  } else if (elevator_floor == 20) {
    CLR(r12, shift_cnt(LIMIT_SWITCH_FLOOR_1));
    CLR(r12, shift_cnt(LIMIT_SWITCH_FLOOR_2));
    CLR(r12, shift_cnt(LIMIT_SWITCH_FLOOR_3));
    SET(r12, shift_cnt(LIMIT_SWITCH_FLOOR_2));
  } else if (elevator_floor == 10) {
    CLR(r12, shift_cnt(LIMIT_SWITCH_FLOOR_1));
    CLR(r12, shift_cnt(LIMIT_SWITCH_FLOOR_2));
    CLR(r12, shift_cnt(LIMIT_SWITCH_FLOOR_3));
    SET(r12, shift_cnt(LIMIT_SWITCH_FLOOR_1));
  }else{
    CLR(r12, shift_cnt(LIMIT_SWITCH_FLOOR_1));
    CLR(r12, shift_cnt(LIMIT_SWITCH_FLOOR_2));
    CLR(r12, shift_cnt(LIMIT_SWITCH_FLOOR_3));
  }

  // DOOR_LIMIT_----: door sensor
  if (door_level == 0) {
    CLR(r12, shift_cnt(DOOR_LIMIT_OPEN));
    SET(r12, shift_cnt(DOOR_LIMIT_CLOSE));
  } else if (door_level == 10) {
    CLR(r12, shift_cnt(DOOR_LIMIT_CLOSE));
    SET(r12, shift_cnt(DOOR_LIMIT_OPEN));
    //SET(r7, shift_cnt(DOOR_CNT));
  } else{
    CLR(r12, shift_cnt(DOOR_LIMIT_CLOSE));
    CLR(r12, shift_cnt(DOOR_LIMIT_OPEN));
  }

  if (input == 1) {
    fprintf(stdout, "Push External calling 1 button\n");
    SET(r12, shift_cnt(EXTERNAL_CALLING_BUTTON_1));
    what_floor();
    CLR(r12, shift_cnt(EXTERNAL_CALLING_BUTTON_1));
  } else if (input == 2) {
    fprintf(stdout, "Push External calling 2\n");
    SET(r12, shift_cnt(EXTERNAL_CALLING_BUTTON_2));
    what_floor();
    CLR(r12, shift_cnt(EXTERNAL_CALLING_BUTTON_2));
  } else if (input == 3) {
    fprintf(stdout, "Push External calling 3\n");
    SET(r12, shift_cnt(EXTERNAL_CALLING_BUTTON_3));
    what_floor();
    CLR(r12, shift_cnt(EXTERNAL_CALLING_BUTTON_3));
  } else {
    int tmp1 = elevator_floor / 10;
    int tmp2 = elevator_floor % 10;
    if (door_level == 0){
      printf("Floor: %1d.%1dF - Door closed\n", tmp1, tmp2);
    }
    else if (door_level == 10){
      printf("Floor: %1d.%1dF - Door opened\n", tmp1, tmp2);
    }
    else{
      printf("Floor: %1d.%1dF - Door moving\n", tmp1, tmp2);
    }
    usleep(1000000);
    what_floor();
  }
  return 0;
}


int run() {
  // initail setting
  init_state();

  fd_set readfds, tmpfds;
  struct timeval tv = {1L, 300L};
  FD_ZERO(&readfds);
  FD_SET(STDIN_FILENO, &readfds); /* set the stdin in the set of file
                                     descriptors to be selected */
  while (1) {
    tmpfds = readfds;
    tv.tv_sec = 1L;
    tv.tv_usec = 300L;
    int count = select(STDIN_FILENO + 1, &tmpfds, NULL, NULL, &tv);
    if (count == -1 || count == 0) {
      simulation(-1);
    } else {
      if (FD_ISSET(STDIN_FILENO, &tmpfds)) {
        char input;
        read(STDIN_FILENO, &input, sizeof(input));
        if (input == 'x') {
          return -1;
        }
        simulation((unsigned int)input - '0');
      }
    }
  }
}

