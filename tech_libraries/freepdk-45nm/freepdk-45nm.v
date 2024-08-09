// 
// ******************************************************************************
// *                                                                            *
// *                   Copyright (C) 2004-2010, Nangate Inc.                    *
// *                           All rights reserved.                             *
// *                                                                            *
// * Nangate and the Nangate logo are trademarks of Nangate Inc.                *
// *                                                                            *
// * All trademarks, logos, software marks, and trade names (collectively the   *
// * "Marks") in this program are proprietary to Nangate or other respective    *
// * owners that have granted Nangate the right and license to use such Marks.  *
// * You are not permitted to use the Marks without the prior written consent   *
// * of Nangate or such third party that may own the Marks.                     *
// *                                                                            *
// * This file has been provided pursuant to a License Agreement containing     *
// * restrictions on its use. This file contains valuable trade secrets and     *
// * proprietary information of Nangate Inc., and is protected by U.S. and      *
// * international laws and/or treaties.                                        *
// *                                                                            *
// * The copyright notice(s) in this file does not indicate actual or intended  *
// * publication of this file.                                                  *
// *                                                                            *
// *      NGLibraryCharacterizer, Development_version - build 201012062042      *
// *                                                                            *
// ******************************************************************************
// 
// * Default delays
//   * comb. path delay        : 0.1
//   * seq. path delay         : 0.1
//   * delay cells             : 0.1
//   * timing checks           : 0.1
// 
// * NTC Setup
//   * Export NTC sections     : true
//   * Combine setup / hold    : true
//   * Combine recovery/removal: true
// 
// * Extras
//   * Export `celldefine      : false
//   * Export `timescale       : -
// 
/* verilator lint_off IMPLICIT */
/* verilator lint_off DECLFILENAME */
/* verilator lint_off UNUSEDPARAM */
module AND2_X1 (A1, A2, ZN);
  input A1;
  input A2;
  output ZN;

  and(ZN, A1, A2);

endmodule

module AND2_X2 (A1, A2, ZN);
  input A1;
  input A2;
  output ZN;

  and(ZN, A1, A2);


endmodule

module AND2_X4 (A1, A2, ZN);
  input A1;
  input A2;
  output ZN;

  and(ZN, A1, A2);

endmodule

module AND3_X1 (A1, A2, A3, ZN);
  input A1;
  input A2;
  input A3;
  output ZN;

  and(ZN, i_4, A3);
  and(i_4, A1, A2);


endmodule

module AND3_X2 (A1, A2, A3, ZN);
  input A1;
  input A2;
  input A3;
  output ZN;

  and(ZN, i_4, A3);
  and(i_4, A1, A2);


endmodule

module AND3_X4 (A1, A2, A3, ZN);
  input A1;
  input A2;
  input A3;
  output ZN;

  and(ZN, i_4, A3);
  and(i_4, A1, A2);


endmodule

module AND4_X1 (A1, A2, A3, A4, ZN);
  input A1;
  input A2;
  input A3;
  input A4;
  output ZN;

  and(ZN, i_8, A4);
  and(i_8, i_9, A3);
  and(i_9, A1, A2);


endmodule

module AND4_X2 (A1, A2, A3, A4, ZN);
  input A1;
  input A2;
  input A3;
  input A4;
  output ZN;

  and(ZN, i_8, A4);
  and(i_8, i_9, A3);
  and(i_9, A1, A2);


endmodule

module AND4_X4 (A1, A2, A3, A4, ZN);
  input A1;
  input A2;
  input A3;
  input A4;
  output ZN;

  and(ZN, i_8, A4);
  and(i_8, i_9, A3);
  and(i_9, A1, A2);


endmodule

module ANTENNA_X1 (A);
  input A;

endmodule

module BUF_X1 (A, Z);
  input A;
  output Z;

  buf(Z, A);


endmodule

module BUF_X16 (A, Z);
  input A;
  output Z;

  buf(Z, A);


endmodule

module BUF_X2 (A, Z);
  input A;
  output Z;

  buf(Z, A);


endmodule

module BUF_X32 (A, Z);
  input A;
  output Z;

  buf(Z, A);

endmodule

module BUF_X4 (A, Z);
  input A;
  output Z;

  buf(Z, A);


endmodule

module BUF_X8 (A, Z);
  input A;
  output Z;

  buf(Z, A);


endmodule

module FA_X1 (A, B, CI, CO, S);
  input A;
  input B;
  input CI;
  output CO;
  output S;

  or(CO, i_16, i_17);
  and(i_16, A, B);
  and(i_17, CI, i_18);
  or(i_18, A, B);
  xor(S, CI, i_22);
  xor(i_22, A, B);


endmodule

module WELLTAP_X1 ();

endmodule

module FILLCELL_X1 ();

endmodule

module FILLCELL_X2 ();

endmodule

module FILLCELL_X4 ();

endmodule

module FILLCELL_X8 ();

endmodule

module FILLCELL_X16 ();

endmodule

module FILLCELL_X32 ();

endmodule

module HA_X1 (A, B, CO, S);
  input A;
  input B;
  output CO;
  output S;

  and(CO, A, B);
  xor(S, A, B);


endmodule

module INV_X1 (A, ZN);
  input A;
  output ZN;

  not(ZN, A);


endmodule

module INV_X16 (A, ZN);
  input A;
  output ZN;

  not(ZN, A);


endmodule

module INV_X2 (A, ZN);
  input A;
  output ZN;

  not(ZN, A);


endmodule

module INV_X32 (A, ZN);
  input A;
  output ZN;

  not(ZN, A);


endmodule

module INV_X4 (A, ZN);
  input A;
  output ZN;

  not(ZN, A);


endmodule

module INV_X8 (A, ZN);
  input A;
  output ZN;

  not(ZN, A);


endmodule

module LOGIC0_X1 (Z);
  output Z;

  buf(Z, 0);
endmodule

module LOGIC1_X1 (Z);
  output Z;

  buf(Z, 1);
endmodule


module NAND2_X1 (A1, A2, ZN);
  input A1;
  input A2;
  output ZN;

  not(ZN, i_10);
  and(i_10, A1, A2);


endmodule

module NAND2_X2 (A1, A2, ZN);
  input A1;
  input A2;
  output ZN;

  not(ZN, i_22);
  and(i_22, A1, A2);


endmodule

module NAND2_X4 (A1, A2, ZN);
  input A1;
  input A2;
  output ZN;

  not(ZN, i_10);
  and(i_10, A1, A2);


endmodule

module NAND3_X1 (A1, A2, A3, ZN);
  input A1;
  input A2;
  input A3;
  output ZN;

  not(ZN, i_8);
  and(i_8, i_9, A3);
  and(i_9, A1, A2);


endmodule

module NAND3_X2 (A1, A2, A3, ZN);
  input A1;
  input A2;
  input A3;
  output ZN;

  not(ZN, i_8);
  and(i_8, i_9, A3);
  and(i_9, A1, A2);


endmodule

module NAND3_X4 (A1, A2, A3, ZN);
  input A1;
  input A2;
  input A3;
  output ZN;

  not(ZN, i_8);
  and(i_8, i_9, A3);
  and(i_9, A1, A2);


endmodule

module NAND4_X1 (A1, A2, A3, A4, ZN);
  input A1;
  input A2;
  input A3;
  input A4;
  output ZN;

  not(ZN, i_12);
  and(i_12, i_13, A4);
  and(i_13, i_14, A3);
  and(i_14, A1, A2);

endmodule

module NAND4_X2 (A1, A2, A3, A4, ZN);
  input A1;
  input A2;
  input A3;
  input A4;
  output ZN;

  not(ZN, i_12);
  and(i_12, i_13, A4);
  and(i_13, i_14, A3);
  and(i_14, A1, A2);


endmodule

module NAND4_X4 (A1, A2, A3, A4, ZN);
  input A1;
  input A2;
  input A3;
  input A4;
  output ZN;

  not(ZN, i_12);
  and(i_12, i_13, A4);
  and(i_13, i_14, A3);
  and(i_14, A1, A2);


endmodule

module NOR2_X1 (A1, A2, ZN);
  input A1;
  input A2;
  output ZN;

  not(ZN, i_10);
  or(i_10, A1, A2);


endmodule

module NOR2_X2 (A1, A2, ZN);
  input A1;
  input A2;
  output ZN;

  not(ZN, i_10);
  or(i_10, A1, A2);


endmodule

module NOR2_X4 (A1, A2, ZN);
  input A1;
  input A2;
  output ZN;

  not(ZN, i_16);
  or(i_16, A1, A2);

endmodule

module NOR3_X1 (A1, A2, A3, ZN);
  input A1;
  input A2;
  input A3;
  output ZN;

  not(ZN, i_8);
  or(i_8, i_9, A3);
  or(i_9, A1, A2);


endmodule

module NOR3_X2 (A1, A2, A3, ZN);
  input A1;
  input A2;
  input A3;
  output ZN;

  not(ZN, i_8);
  or(i_8, i_9, A3);
  or(i_9, A1, A2);


endmodule

module NOR3_X4 (A1, A2, A3, ZN);
  input A1;
  input A2;
  input A3;
  output ZN;

  not(ZN, i_8);
  or(i_8, i_9, A3);
  or(i_9, A1, A2);


endmodule

module NOR4_X1 (A1, A2, A3, A4, ZN);
  input A1;
  input A2;
  input A3;
  input A4;
  output ZN;

  not(ZN, i_12);
  or(i_12, i_13, A4);
  or(i_13, i_14, A3);
  or(i_14, A1, A2);


endmodule

module NOR4_X2 (A1, A2, A3, A4, ZN);
  input A1;
  input A2;
  input A3;
  input A4;
  output ZN;

  not(ZN, i_12);
  or(i_12, i_13, A4);
  or(i_13, i_14, A3);
  or(i_14, A1, A2);


endmodule

module NOR4_X4 (A1, A2, A3, A4, ZN);
  input A1;
  input A2;
  input A3;
  input A4;
  output ZN;

  not(ZN, i_12);
  or(i_12, i_13, A4);
  or(i_13, i_14, A3);
  or(i_14, A1, A2);


endmodule

module OAI211_X1 (A, B, C1, C2, ZN);
  input A;
  input B;
  input C1;
  input C2;
  output ZN;

  not(ZN, i_12);
  and(i_12, i_13, B);
  and(i_13, i_14, A);
  or(i_14, C1, C2);


endmodule

module OAI211_X2 (A, B, C1, C2, ZN);
  input A;
  input B;
  input C1;
  input C2;
  output ZN;

  not(ZN, i_12);
  and(i_12, i_13, B);
  and(i_13, i_14, A);
  or(i_14, C1, C2);


endmodule

module OAI211_X4 (A, B, C1, C2, ZN);
  input A;
  input B;
  input C1;
  input C2;
  output ZN;

  not(ZN, i_12);
  and(i_12, i_13, B);
  and(i_13, i_14, A);
  or(i_14, C1, C2);


endmodule

module OAI21_X1 (A, B1, B2, ZN);
  input A;
  input B1;
  input B2;
  output ZN;

  not(ZN, i_8);
  and(i_8, A, i_9);
  or(i_9, B1, B2);

endmodule

module OAI21_X2 (A, B1, B2, ZN);
  input A;
  input B1;
  input B2;
  output ZN;

  not(ZN, i_8);
  and(i_8, A, i_9);
  or(i_9, B1, B2);


endmodule

module OAI21_X4 (A, B1, B2, ZN);
  input A;
  input B1;
  input B2;
  output ZN;

  not(ZN, i_8);
  and(i_8, A, i_9);
  or(i_9, B1, B2);


endmodule

module OAI221_X1 (A, B1, B2, C1, C2, ZN);
  input A;
  input B1;
  input B2;
  input C1;
  input C2;
  output ZN;

  not(ZN, i_16);
  and(i_16, i_17, i_19);
  and(i_17, i_18, A);
  or(i_18, C1, C2);
  or(i_19, B1, B2);


endmodule

module OAI221_X2 (A, B1, B2, C1, C2, ZN);
  input A;
  input B1;
  input B2;
  input C1;
  input C2;
  output ZN;

  not(ZN, i_16);
  and(i_16, i_17, i_19);
  and(i_17, i_18, A);
  or(i_18, C1, C2);
  or(i_19, B1, B2);

endmodule

module OAI221_X4 (A, B1, B2, C1, C2, ZN);
  input A;
  input B1;
  input B2;
  input C1;
  input C2;
  output ZN;

  not(ZN, i_24);
  not(i_24, i_25);
  not(i_25, i_26);
  and(i_26, i_27, i_29);
  and(i_27, i_28, A);
  or(i_28, C1, C2);
  or(i_29, B1, B2);

endmodule

module OAI222_X1 (A1, A2, B1, B2, C1, C2, ZN);
  input A1;
  input A2;
  input B1;
  input B2;
  input C1;
  input C2;
  output ZN;

  not(ZN, i_20);
  and(i_20, i_21, i_24);
  and(i_21, i_22, i_23);
  or(i_22, A1, A2);
  or(i_23, B1, B2);
  or(i_24, C1, C2);


endmodule

module OAI222_X2 (A1, A2, B1, B2, C1, C2, ZN);
  input A1;
  input A2;
  input B1;
  input B2;
  input C1;
  input C2;
  output ZN;

  not(ZN, i_20);
  and(i_20, i_21, i_24);
  and(i_21, i_22, i_23);
  or(i_22, A1, A2);
  or(i_23, B1, B2);
  or(i_24, C1, C2);


endmodule

module OAI222_X4 (A1, A2, B1, B2, C1, C2, ZN);
  input A1;
  input A2;
  input B1;
  input B2;
  input C1;
  input C2;
  output ZN;

  not(ZN, i_28);
  not(i_28, i_29);
  not(i_29, i_30);
  and(i_30, i_31, i_34);
  and(i_31, i_32, i_33);
  or(i_32, A1, A2);
  or(i_33, B1, B2);
  or(i_34, C1, C2);


endmodule

module OAI22_X1 (A1, A2, B1, B2, ZN);
  input A1;
  input A2;
  input B1;
  input B2;
  output ZN;

  not(ZN, i_12);
  and(i_12, i_13, i_14);
  or(i_13, A1, A2);
  or(i_14, B1, B2);


endmodule

module OAI22_X2 (A1, A2, B1, B2, ZN);
  input A1;
  input A2;
  input B1;
  input B2;
  output ZN;

  not(ZN, i_12);
  and(i_12, i_13, i_14);
  or(i_13, A1, A2);
  or(i_14, B1, B2);

endmodule

module OAI22_X4 (A1, A2, B1, B2, ZN);
  input A1;
  input A2;
  input B1;
  input B2;
  output ZN;

  not(ZN, i_12);
  and(i_12, i_13, i_14);
  or(i_13, A1, A2);
  or(i_14, B1, B2);

endmodule

module OAI33_X1 (A1, A2, A3, B1, B2, B3, ZN);
  input A1;
  input A2;
  input A3;
  input B1;
  input B2;
  input B3;
  output ZN;

  not(ZN, i_20);
  and(i_20, i_21, i_23);
  or(i_21, i_22, A3);
  or(i_22, A1, A2);
  or(i_23, i_24, B3);
  or(i_24, B1, B2);


endmodule

module OR2_X1 (A1, A2, ZN);
  input A1;
  input A2;
  output ZN;

  or(ZN, A1, A2);


endmodule

module OR2_X2 (A1, A2, ZN);
  input A1;
  input A2;
  output ZN;

  or(ZN, A1, A2);


endmodule

module OR2_X4 (A1, A2, ZN);
  input A1;
  input A2;
  output ZN;

  or(ZN, A1, A2);


endmodule

module OR3_X1 (A1, A2, A3, ZN);
  input A1;
  input A2;
  input A3;
  output ZN;

  or(ZN, i_4, A3);
  or(i_4, A1, A2);


endmodule

module OR3_X2 (A1, A2, A3, ZN);
  input A1;
  input A2;
  input A3;
  output ZN;

  or(ZN, i_4, A3);
  or(i_4, A1, A2);


endmodule

module OR3_X4 (A1, A2, A3, ZN);
  input A1;
  input A2;
  input A3;
  output ZN;

  or(ZN, i_4, A3);
  or(i_4, A1, A2);


endmodule

module OR4_X1 (A1, A2, A3, A4, ZN);
  input A1;
  input A2;
  input A3;
  input A4;
  output ZN;

  or(ZN, i_8, A4);
  or(i_8, i_9, A3);
  or(i_9, A1, A2);


endmodule

module OR4_X2 (A1, A2, A3, A4, ZN);
  input A1;
  input A2;
  input A3;
  input A4;
  output ZN;

  or(ZN, i_8, A4);
  or(i_8, i_9, A3);
  or(i_9, A1, A2);


endmodule

module OR4_X4 (A1, A2, A3, A4, ZN);
  input A1;
  input A2;
  input A3;
  input A4;
  output ZN;

  or(ZN, i_8, A4);
  or(i_8, i_9, A3);
  or(i_9, A1, A2);


endmodule


module TBUF_X1 (A, EN, Z);
  input A;
  input EN;
  output Z;

  bufif0(Z, Z_in, Z_enable);
  buf(Z_enable, EN);
  buf(Z_in, A);

endmodule

module TBUF_X16 (A, EN, Z);
  input A;
  input EN;
  output Z;

  bufif0(Z, Z_in, Z_enable);
  buf(Z_enable, EN);
  buf(Z_in, A);


endmodule

module TBUF_X2 (A, EN, Z);
  input A;
  input EN;
  output Z;

  bufif0(Z, Z_in, Z_enable);
  buf(Z_enable, EN);
  buf(Z_in, A);


endmodule

module TBUF_X4 (A, EN, Z);
  input A;
  input EN;
  output Z;

  bufif0(Z, Z_in, Z_enable);
  buf(Z_enable, EN);
  buf(Z_in, A);

endmodule

module TBUF_X8 (A, EN, Z);
  input A;
  input EN;
  output Z;

  bufif0(Z, Z_in, Z_enable);
  buf(Z_enable, EN);
  buf(Z_in, A);

endmodule

module TINV_X1 (EN, I, ZN);
  input EN;
  input I;
  output ZN;

  bufif0(ZN, ZN_in, ZN_enable);
  buf(ZN_enable, EN);
  not(ZN_in, I);

endmodule


module XNOR2_X1 (A, B, ZN);
  input A;
  input B;
  output ZN;

  not(ZN, i_4);
  xor(i_4, A, B);


endmodule

module XNOR2_X2 (A, B, ZN);
  input A;
  input B;
  output ZN;

  not(ZN, i_4);
  xor(i_4, A, B);


endmodule

module XOR2_X1 (A, B, Z);
  input A;
  input B;
  output Z;

  xor(Z, A, B);


endmodule

module XOR2_X2 (A, B, Z);
  input A;
  input B;
  output Z;

  xor(Z, A, B);


endmodule

primitive \seq_DFF_X1  (IQ, nextstate, CK, NOTIFIER);
  output IQ;
  input nextstate;
  input CK;
  input NOTIFIER;
  reg IQ;

  table
// nextstate          CK    NOTIFIER     : @IQ :          IQ
           0           r           ?       : ? :           0;
           1           r           ?       : ? :           1;
           0           *           ?       : 0 :           0; // reduce pessimism
           1           *           ?       : 1 :           1; // reduce pessimism
           *           ?           ?       : ? :           -; // Ignore all edges on nextstate
           ?           n           ?       : ? :           -; // Ignore non-triggering clock edge
           ?           ?           *       : ? :           x; // Any NOTIFIER change
  endtable
endprimitive

module DFF_X1 (D, CK, Q, QN);
  input D;
  input CK;
  output reg Q /* verilator public_flat_rw */;
  output reg QN /* verilator public_flat_rw */;

  always @(posedge CK) begin
    Q <= D;
    QN <= ~D;
  end

endmodule

//
// End of file
//
/* verilator lint_on IMPLICIT */
/* verilator lint_on DECLFILENAME */
/* verilator lint_on UNUSEDPARAM */
