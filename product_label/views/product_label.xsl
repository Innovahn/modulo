<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:fo="http://www.w3.org/1999/XSL/Format">

 <xsl:template match="lots">
 	<document >
		 <template pageSize="(62mm, 29mm)" 
			  leftMargin="1.4mm" rightMargin="1.4mm" topMargin="0mm" bottomMargin="0mm" 
			  title="Bar Codes" author="Generated by Pedro Cabrera">
		 <pageTemplate id="all">
		    <frame id="first" x1="0" y1="0" width="62mm" height="29mm"/>
		 </pageTemplate>
		 </template>
		 	<stylesheet>
					 <paraStyle name="st_pn"      fontName="Helvetica" leading="10" fontSize="10" spaceBefore="1mm" spaceAfter="0" alignment="center"/>
					 <paraStyle name="st_product" fontName="Helvetica" leading="7" fontSize="7"  spaceBefore="0"   spaceAfter="0"/>
					 <paraStyle name="st_loc"     fontName="Helvetica" leading="0" fontSize="7"  spaceBefore="0"   spaceAfter="0" alignment="center"/>
					 <paraStyle name="st_slogan"  fontName="Helvetica" leading="0" fontSize="7"  spaceBefore="0"   spaceAfter="0" alignment="left"/>

<paraStyle name="sc_color"  fontName="Helvetica" leading="0" fontSize="5"  spaceBefore="0"   spaceAfter="0" alignment="left"/>

					 <paraStyle name="st_variant"  fontName="Helvetica" leading="0" fontSize="7"  spaceBefore="0"   spaceAfter="0" alignment="left"/>
		 			
			</stylesheet>
		 <story>
		 	<xsl:apply-templates select="lot-line" mode="story"/>
		 </story>
	 </document>
 </xsl:template>

 <xsl:template match="lot-line" mode="story">

        <para style="st_product"><xsl:value-of select="product"/> </para> <para> <xsl:value-of select="sc_color"/></para>
	<!--<product type="field" name="name"/>-->
        <barCode code="ean13" barWidth="1.0" barHeight="40.0">
            <xsl:value-of select="ean13"/>
        </barCode>
        <!--<para style="st_pn"><xsl:value-of select="code"/></para>
        <spacer length="1mm"/>-->
	<para style="st_variant"><xsl:value-of  select="variant"/>
	    <!-- <xsl:value-of select="variant"/>--><!--<product type="field" name="default_code"/>-->

	</para>
	
        <para></para>
	 <para style="st_loc">
           <xsl:value-of  select="loc_rack"/>: <xsl:value-of  select="loc_row"/> : <xsl:value-of  select="loc_case"/>
        </para>
<nextFrame/>
       <!--<para style="st_slogan">
            Company Slogan
        </para>
        <para style="st_loc">
            <xsl:value-of select="loc_rack"/> : <xsl:value-of select="loc_row"/> : <xsl:value-of select="loc_case"/>
        </para>-->
 </xsl:template>

</xsl:stylesheet>
