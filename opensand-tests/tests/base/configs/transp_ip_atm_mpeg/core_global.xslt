<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
<xsl:output method="xml" indent="yes" encoding="UTF-8"/>

<xsl:template name="Newline">
<xsl:text>
        </xsl:text>
</xsl:template>

<xsl:template match="@*|node()">
    <xsl:copy>
        <xsl:apply-templates select="@*|node()"/>
    </xsl:copy> 
</xsl:template>

<xsl:template match="satellite_type">
    <satellite_type>transparent</satellite_type>
</xsl:template>

<xsl:template match="return_up_encap_schemes">
        <return_up_encap_schemes>
    <xsl:call-template name="Newline" />
                <encap_scheme pos="0" encap="AAL5/ATM" />
    <xsl:call-template name="Newline" />
        </return_up_encap_schemes>
</xsl:template>


<xsl:template match="forward_down_encap_schemes">
        <forward_down_encap_schemes>
    <xsl:call-template name="Newline" />
                <encap_scheme pos="0" encap="ULE" />
    <xsl:call-template name="Newline" />
                <encap_scheme pos="1" encap="MPEG2-TS" />
    <xsl:call-template name="Newline" />
        </forward_down_encap_schemes>
</xsl:template>


</xsl:stylesheet>

